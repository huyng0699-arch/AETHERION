"""Authenticated, source-aware native Personal Health view.

Q-0077 integrates Mission -> Personal by passing the *same explicit subject ID*
and ephemeral in-memory bearer token to the canonical HTTP API. No person,
health reading or access right is synthesized; the server is the authority.
"""
from __future__ import annotations

import json

from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QTableWidgetItem, QWidget

from .identity import checked_personal_handoff
from .latest_metrics import latest_metric_cards
from .personal_visual import build_personal_visual, update_personal_tiles, latest_tiles
from .source_classification import record_origin
from .today_dashboard import (
    build_personal_today_snapshot,
    personal_observations_url,
)


class AuthorizedPersonalTodayPage(QWidget):
    """Native Qt Personal Today page driven by authenticated observations."""

    def __init__(self, api_url: str, network, parent=None):
        super().__init__(parent)
        self._api_url = api_url.rstrip("/")
        self._network = network
        self._subject_id = ""
        self._token = ""
        self._request_seq = 0
        self._displayed_cards = ()

        self._visible_cards = ()
        build_personal_visual(self)

    @property
    def selected_subject_id(self) -> str:
        return self._subject_id

    def select_subject(self, subject_id: str, access_token: str) -> None:
        """Change subject atomically; never display the previous subject's records."""
        self._request_seq += 1  # invalidate any in-flight reply from prior subject
        self._displayed_cards = ()
        self._visible_cards = ()
        self.table.setRowCount(0)
        update_personal_tiles(self, ())
        self._subject_id = ""
        self._token = ""
        try:
            subject, token = checked_personal_handoff(subject_id, access_token)
        except ValueError:
            self.subject_label.setText("No authorized subject selected")
            self.status_label.setText("DENIED — invalid subject or missing session")
            return
        self._subject_id = subject
        self._token = token
        self.subject_label.setText(f"Subject: {subject}")
        self.status_label.setText("Loading authenticated observations…")
        self.refresh()

    def refresh(self) -> None:
        if not self._subject_id or not self._token:
            self._displayed_cards = ()
            self._visible_cards = ()
            self.table.setRowCount(0)
            update_personal_tiles(self, ())
            self.status_label.setText("DENIED — select a subject from Mission Control and sign in")
            return
        self._request_seq += 1
        seq, subject = self._request_seq, self._subject_id
        self._displayed_cards = ()
        self._visible_cards = ()
        self.table.setRowCount(0)
        update_personal_tiles(self, ())
        request = QNetworkRequest(QUrl(personal_observations_url(self._api_url, subject)))
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode("utf-8"))
        self.status_label.setText(f"Loading subject {subject} from local API…")
        reply = self._network.get(request)
        reply.finished.connect(lambda: self._on_reply(reply, subject, seq))

    def _on_reply(self, reply, subject_id: str, seq: int) -> None:
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        network_error = reply.error() != QNetworkReply.NetworkError.NoError
        raw = bytes(reply.readAll())
        reply.deleteLater()
        if seq != self._request_seq or subject_id != self._subject_id:
            return  # stale/superseded reply must never expose another subject
        if status_code in (401, 403):
            self.table.setRowCount(0)
            if status_code == 401:
                self._token = ""
            snapshot = build_personal_today_snapshot(
                {}, subject_id, denied=True
            )
        elif network_error or status_code is None:
            snapshot = build_personal_today_snapshot({}, subject_id, offline=True)
        elif status_code != 200:
            self.table.setRowCount(0)
            self.status_label.setText("ERROR — server refused observations request")
            return
        else:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                payload = {}
            snapshot = build_personal_today_snapshot(payload, subject_id)

        try:
            displayed = latest_metric_cards(snapshot.cards)
        except ValueError:
            self.table.setRowCount(0)
            self.status_label.setText("ERROR — latest metric provenance is invalid")
            return
        self.status_label.setText(f"{snapshot.state} — {snapshot.status_note}")
        self._displayed_cards = displayed
        self._render_rows()
        if snapshot.has_more:
            self.note.setText(
                "Showing the newest record per metric, scope and unit from the "
                "latest 50 server observations. More history is available."
            )
        else:
            self.note.setText(
                "Newest recorded value per metric, scope and unit. Older records "
                "remain on the server; missing readings are not normal readings."
            )

    def _render_rows(self, *_):
        """Filter by explicit provenance, never infer device origin from metric."""
        mode = self.origin_filter.currentData()
        visible = [
            card for card in self._displayed_cards
            if mode == "all" or record_origin(card)[0] == mode
        ]
        self._visible_cards = tuple(visible)
        update_personal_tiles(self, self._visible_cards)
        self.table.setRowCount(len(visible))
        for row, card in enumerate(visible):
            label = record_origin(card)[1]
            values = (
                card.metric, card.reading, card.observed_at,
                card.source_id, card.scope, card.quality, card.verification_state, label
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def focus_metric_tile(self, tile_id: str) -> None:
        """Reveal the actual source row behind a card, never a fabricated detail."""
        card = latest_tiles(self._visible_cards).get(tile_id)
        if card is None:
            return
        for index, visible in enumerate(self._visible_cards):
            if (visible.metric == card.metric and visible.observed_at == card.observed_at
                    and visible.source_id == card.source_id and visible.reading == card.reading):
                self.table.selectRow(index)
                self.table.scrollToItem(self.table.item(index, 0))
                self.table.setFocus()
                self.workspace_scroll.ensureWidgetVisible(self.records_panel)
                break
