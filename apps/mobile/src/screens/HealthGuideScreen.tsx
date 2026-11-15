import React, { useState } from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppHeader, AppPage, Body, Panel, Title } from '../components/ui';
import { ThemeColors, useThemedStyles } from '../theme';
import { Locale } from '../types';
import { copy } from '../uiCopy';

type Localized = Record<Locale, string>;
type MetricIcon = keyof typeof Ionicons.glyphMap;
type GuideSource = { label: string; url: string };
type MetricGuide = {
  id: string;
  name: string;
  icon: MetricIcon;
  measures: Localized;
  purpose: Localized;
  tip: Localized;
  sources: GuideSource[];
};

const guides: MetricGuide[] = [
  {
    id: 'pulse', name: 'Heart rate / Pulse', icon: 'heart-outline',
    measures: { en: 'Heartbeats per minute (bpm). The rate changes with movement, rest, posture, medicines, and other conditions.', vi: 'Số nhịp tim mỗi phút (bpm). Nhịp có thể đổi theo vận động, nghỉ ngơi, tư thế, thuốc và tình trạng cơ thể.' },
    purpose: { en: 'It helps track how your heart responds over time. A pulse value alone cannot confirm an abnormal rhythm.', vi: 'Chỉ số giúp theo dõi tim thay đổi theo thời gian. Một số đo mạch riêng lẻ không xác nhận rối loạn nhịp.' },
    tip: { en: 'Record the time and whether you were resting or exercising. Compare readings taken in similar conditions.', vi: 'Ghi thời điểm và bạn đang nghỉ hay vận động. So sánh các lần đo trong điều kiện tương tự.' },
    sources: [
      { label: 'MedlinePlus — Vital signs', url: 'https://medlineplus.gov/vitalsigns.html' },
      { label: 'NASA — Arrhythmia evidence', url: 'https://humanresearchroadmap.nasa.gov/evidence/other/arrhythmia.pdf' },
    ],
  },
  {
    id: 'blood-pressure', name: 'Blood pressure', icon: 'speedometer-outline',
    measures: { en: 'Two values: systolic pressure while the heart beats, and diastolic pressure between beats. The unit is usually mmHg.', vi: 'Hai số: huyết áp tâm thu khi tim co bóp và tâm trương giữa các nhịp. Đơn vị thường là mmHg.' },
    purpose: { en: 'It describes pressure in the arteries. Posture, activity, food, and medicines can change a reading.', vi: 'Chỉ số cho biết áp lực trong động mạch. Tư thế, vận động, thức ăn và thuốc có thể làm kết quả thay đổi.' },
    tip: { en: 'Use the assigned cuff and method. Keep both numbers with the unit, time, arm, and posture.', vi: 'Dùng máy đo và cách đo được hướng dẫn. Ghi đủ hai số, đơn vị, thời điểm, tay và tư thế.' },
    sources: [{ label: 'MedlinePlus — Measuring blood pressure', url: 'https://medlineplus.gov/lab-tests/measuring-blood-pressure/' }],
  },
  {
    id: 'breathing', name: 'Breathing rate', icon: 'leaf-outline',
    measures: { en: 'Breaths per minute; one inhale-and-exhale cycle is one breath.', vi: 'Số nhịp thở mỗi phút; một lần hít vào và thở ra là một nhịp.' },
    purpose: { en: 'Rate and pattern help the medical team assess breathing alongside symptoms and activity.', vi: 'Tần số và kiểu thở giúp nhân viên y tế đánh giá hô hấp cùng triệu chứng và mức vận động.' },
    tip: { en: 'Record whether it was measured at rest, after exercise, or during symptoms. Report new breathing difficulty promptly.', vi: 'Ghi rõ đo lúc nghỉ, sau vận động hay khi có triệu chứng. Báo sớm khi xuất hiện khó thở mới.' },
    sources: [{ label: 'MedlinePlus — Vital signs', url: 'https://medlineplus.gov/vitalsigns.html' }],
  },
  {
    id: 'temperature', name: 'Body temperature', icon: 'thermometer-outline',
    measures: { en: 'An estimate of body temperature from a particular device and measurement site.', vi: 'Ước tính nhiệt độ cơ thể bằng thiết bị và vị trí đo cụ thể.' },
    purpose: { en: 'It can support assessment when considered with symptoms and change over time.', vi: 'Nhiệt độ hỗ trợ đánh giá khi được xem cùng triệu chứng và diễn biến theo thời gian.' },
    tip: { en: 'Follow the approved thermometer method. Record the device or site and time; different methods may not compare directly.', vi: 'Làm theo cách dùng nhiệt kế đã được hướng dẫn. Ghi thiết bị hoặc vị trí đo và thời điểm; các cách đo khác nhau có thể không so sánh trực tiếp.' },
    sources: [{ label: 'MedlinePlus — Vital signs', url: 'https://medlineplus.gov/vitalsigns.html' }],
  },
  {
    id: 'oxygen', name: 'Oxygen saturation (SpO₂)', icon: 'water-outline',
    measures: { en: 'A pulse oximeter estimates the share of hemoglobin carrying oxygen. It is not a blood-gas test.', vi: 'Máy đo SpO₂ ước tính tỷ lệ hemoglobin đang mang oxy. Đây không phải xét nghiệm khí máu.' },
    purpose: { en: 'It helps assess oxygenation together with breathing and symptoms. Device readings can be inaccurate.', vi: 'Chỉ số hỗ trợ đánh giá oxy hóa máu cùng tình trạng thở và triệu chứng. Kết quả thiết bị có thể sai lệch.' },
    tip: { en: 'Keep still and follow the sensor instructions until the reading is steady. Cold skin, poor circulation, movement, or nail coverings may affect some devices. Report symptoms even if the number looks normal.', vi: 'Giữ yên và làm theo hướng dẫn cảm biến đến khi số đo ổn định. Da lạnh, tuần hoàn kém, cử động hoặc móng phủ có thể ảnh hưởng một số thiết bị. Báo triệu chứng dù con số trông bình thường.' },
    sources: [{ label: 'MedlinePlus — Pulse oximetry', url: 'https://medlineplus.gov/lab-tests/pulse-oximetry/' }],
  },
  {
    id: 'ecg', name: 'Electrocardiogram (ECG)', icon: 'pulse-outline',
    measures: { en: 'A recording of the electrical signals the heart makes as it beats. The tracing is different from a single pulse number.', vi: 'Bản ghi tín hiệu điện do tim tạo ra khi đập. Đường ghi ECG khác với một con số nhịp tim.' },
    purpose: { en: 'Clinicians use the tracing to review heart rate and rhythm. It needs clinical interpretation and cannot diagnose a condition by itself.', vi: 'Nhân viên y tế dùng đường ghi để xem xét tần số và nhịp tim. ECG cần được diễn giải lâm sàng và không tự chẩn đoán bệnh.' },
    tip: { en: 'Use the assigned device and electrode placement. Record time, activity, and symptoms; do not diagnose from a device label alone.', vi: 'Dùng thiết bị và vị trí điện cực được hướng dẫn. Ghi thời điểm, hoạt động và triệu chứng; không tự chẩn đoán từ nhãn trên thiết bị.' },
    sources: [
      { label: 'MedlinePlus — Electrocardiogram', url: 'https://medlineplus.gov/lab-tests/electrocardiogram/' },
      { label: 'NASA — Arrhythmia evidence', url: 'https://humanresearchroadmap.nasa.gov/evidence/other/arrhythmia.pdf' },
    ],
  },
  {
    id: 'sleep', name: 'Sleep', icon: 'moon-outline',
    measures: { en: 'Sleep duration and timing, often recorded by a diary or device. It is not a vital sign.', vi: 'Thời lượng và thời điểm ngủ, thường ghi bằng nhật ký hoặc thiết bị. Đây không phải dấu hiệu sinh tồn.' },
    purpose: { en: 'NASA research tracks sleep patterns in orbit to study sleep during spaceflight and support crew health and performance.', vi: 'Nghiên cứu NASA theo dõi kiểu ngủ trên quỹ đạo để tìm hiểu giấc ngủ trong chuyến bay và hỗ trợ sức khỏe, hiệu suất phi hành đoàn.' },
    tip: { en: 'Log sleep and wake times plus major interruptions for several days. Tell the medical team if fatigue affects your tasks.', vi: 'Ghi giờ ngủ, giờ thức và những lần gián đoạn chính trong vài ngày. Báo nhân viên y tế nếu mệt mỏi ảnh hưởng công việc.' },
    sources: [{ label: 'NASA — Sleep in Orbit', url: 'https://www.nasa.gov/blogs/stationreport/2024/01/25/iss-daily-summary-report-1-25-2024/' }],
  },
  {
    id: 'radiation', name: 'Radiation exposure', icon: 'radio-outline',
    measures: { en: 'A dosimeter or mission system records an estimate of radiation exposure over a stated period.', vi: 'Liều kế hoặc hệ thống nhiệm vụ ghi nhận ước tính phơi nhiễm bức xạ trong một khoảng thời gian.' },
    purpose: { en: 'Crew exposure differs by location and activity. NASA monitors each crew member so mission teams can manage exposure.', vi: 'Mức phơi nhiễm thay đổi theo vị trí và hoạt động. NASA theo dõi từng thành viên để đội nhiệm vụ quản lý mức phơi nhiễm.' },
    tip: { en: 'Use the assigned monitor and mission rules. Record its unit and date range; you cannot judge radiation exposure by how you feel.', vi: 'Dùng thiết bị theo dõi và quy định nhiệm vụ. Ghi đơn vị, khoảng thời gian; không thể biết mức phơi nhiễm chỉ bằng cảm giác.' },
    sources: [
      { label: 'NASA — Space Radiation', url: 'https://www.nasa.gov/directorates/esdmd/hhp/space-radiation/' },
      { label: 'NASA — Human-System Standard, Vol. 2', url: 'https://www.nasa.gov/reference/6-0-natural-and-induced-environments-vol-2/' },
    ],
  },
  {
    id: 'blood-count', name: 'Complete blood count (CBC)', icon: 'flask-outline',
    measures: { en: 'A lab panel that counts blood cells, including red cells, white cells, and platelets; it may also report hemoglobin and related measures.', vi: 'Xét nghiệm đếm các tế bào máu gồm hồng cầu, bạch cầu và tiểu cầu; có thể kèm hemoglobin và chỉ số liên quan.' },
    purpose: { en: 'Red cells and hemoglobin carry oxygen, white cells support immune defense, and platelets help blood clot.', vi: 'Hồng cầu và hemoglobin vận chuyển oxy, bạch cầu tham gia bảo vệ miễn dịch, tiểu cầu giúp đông máu.' },
    tip: { en: 'Check the exact test, unit, date, and lab reference interval. Ask the medical team to interpret results in your situation.', vi: 'Kiểm tra tên xét nghiệm, đơn vị, ngày lấy mẫu và khoảng tham chiếu của phòng xét nghiệm. Nhờ nhân viên y tế diễn giải theo tình trạng của bạn.' },
    sources: [{ label: 'MedlinePlus — Complete blood count', url: 'https://medlineplus.gov/lab-tests/complete-blood-count-cbc/' }],
  },
];

export function HealthGuideScreen({ locale, onBack }: { locale: Locale; onBack: () => void }) {
  const { colors, styles } = useThemedStyles(buildStyles);
  const [expanded, setExpanded] = useState('pulse');

  return (
    <AppPage>
      <AppHeader title={copy(locale, 'healthGuide')} onBack={onBack} backLabel={copy(locale, 'backToLogin')} />
      <View style={styles.intro}>
        <Title size={22}>{copy(locale, 'healthGuideIntro')}</Title>
        <Text style={styles.note}>{copy(locale, 'healthGuideNote')}</Text>
      </View>

      {guides.map((guide) => {
        const open = expanded === guide.id;
        return (
          <Panel key={guide.id} style={styles.card}>
            <Pressable
              accessibilityRole="button"
              accessibilityState={{ expanded: open }}
              onPress={() => setExpanded(open ? '' : guide.id)}
              style={styles.cardHeader}
            >
              <View style={styles.icon}><Ionicons name={guide.icon} size={19} color={colors.cyan} /></View>
              <Text style={styles.metricTitle}>{guide.name}</Text>
              <Ionicons name={open ? 'chevron-up' : 'chevron-down'} size={18} color={colors.muted} />
            </Pressable>
            {open ? (
              <View style={styles.details}>
                <Info label={copy(locale, 'guideMeasures')} value={guide.measures[locale]} />
                <Info label={copy(locale, 'guidePurpose')} value={guide.purpose[locale]} />
                <Info label={copy(locale, 'guideTip')} value={guide.tip[locale]} />
                <View style={styles.sources}>
                  <Text style={styles.label}>{copy(locale, 'guideSources')}</Text>
                  {guide.sources.map((source) => (
                    <Pressable key={source.url} accessibilityRole="button" accessibilityLabel={source.label} onPress={() => { void Linking.openURL(source.url).catch(() => undefined); }} style={styles.sourceLink}>
                      <Text style={styles.sourceText}>{source.label}</Text>
                      <Ionicons name="open-outline" size={15} color={colors.cyan} />
                    </Pressable>
                  ))}
                </View>
              </View>
            ) : null}
          </Panel>
        );
      })}
    </AppPage>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  const { styles } = useThemedStyles(buildStyles);
  return <View style={styles.info}><Text style={styles.label}>{label}</Text><Text style={styles.body}>{value}</Text></View>;
}

const buildStyles = (colors: ThemeColors) => StyleSheet.create({
  intro: { gap: 8, marginBottom: 2 },
  note: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  card: { gap: 10 },
  cardHeader: { minHeight: 42, flexDirection: 'row', alignItems: 'center', gap: 10 },
  icon: { width: 34, height: 34, borderRadius: 11, backgroundColor: colors.cardSoft, alignItems: 'center', justifyContent: 'center' },
  metricTitle: { flex: 1, color: colors.text, fontSize: 14, fontWeight: '800' },
  details: { gap: 12, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border, paddingTop: 12 },
  info: { gap: 4 },
  label: { color: colors.cyan, fontSize: 11, fontWeight: '800', textTransform: 'uppercase' },
  body: { color: colors.text, fontSize: 13, lineHeight: 19 },
  sources: { gap: 6 },
  sourceLink: { minHeight: 34, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  sourceText: { flex: 1, color: colors.muted, fontSize: 12, textDecorationLine: 'underline' },
});
