import { Locale } from './types';

const messages = {
  vi: {
    brand: 'AETHERION', tagline: 'Một sức khỏe. Một nhân loại. Vượt khỏi Trái Đất.',
    portalEyebrow: 'AETHERION HEALTH', portalTitle: 'Cổng sức khỏe', portalDescription: 'Chọn một không gian để tiếp tục. Dữ liệu sức khỏe chỉ mở sau khi đăng nhập.',
    personal: 'Sức khỏe', personalDesc: 'Hồ sơ và dữ liệu đã được server ghi nhận.',
    monitor: 'Theo dõi', monitorDesc: 'Kiểm tra dữ liệu, nguồn đo và thời điểm ghi.',
    ai: 'AI', aiDesc: 'Trợ lý chỉ hoạt động khi server cung cấp dịch vụ AI.',
    science: 'Thư viện', scienceDesc: 'Tài liệu khoa học có nguồn và trạng thái xác minh.',
    mission: 'Phi hành đoàn', missionDesc: 'Không gian dành cho người dùng được phân quyền.',
    signIn: 'Đăng nhập', signOut: 'Đăng xuất', signInTitle: 'Kết nối với AETHERION', signInSubtitle: 'Dùng tài khoản đã được tạo trên AETHERION Server.',
    serverUrl: 'Địa chỉ server', username: 'Tên đăng nhập', password: 'Mật khẩu', connect: 'Kiểm tra kết nối', connecting: 'Đang kết nối…', signInAction: 'Đăng nhập', signingIn: 'Đang đăng nhập…', cancel: 'Quay lại',
    urlRequired: 'Nhập địa chỉ server trước.', urlInvalid: 'Địa chỉ server không hợp lệ.', urlLocalhost: 'Điện thoại thật cần địa chỉ LAN của máy chủ, không dùng localhost.', urlSaved: 'Đã lưu địa chỉ server trên thiết bị.',
    loginRequired: 'Cần đăng nhập để mở dữ liệu được bảo vệ.', loginFailed: 'Không đăng nhập được. Kiểm tra tài khoản, mật khẩu và server.', serverOnline: 'Server phản hồi', serverOffline: 'Chưa kết nối server',
    home: 'Trang đầu', settings: 'Cài đặt', language: 'Ngôn ngữ', vietnamese: 'Tiếng Việt', english: 'English', notSignedIn: 'Chưa đăng nhập',
    healthTitle: 'Sức khỏe', monitorTitle: 'Theo dõi', missionTitle: 'Phi hành đoàn',
    loading: 'Đang tải dữ liệu…', refresh: 'Tải lại', noData: 'Chưa có dữ liệu', noDataNote: 'Chưa có dữ liệu. Trạng thái chưa xác định.',
    availability: 'Trạng thái dữ liệu', observations: 'Số quan sát', latest: 'Ghi nhận gần nhất', metrics: 'Chỉ số đã ghi',
    subject: 'Đối tượng dữ liệu', noSubject: 'Không có đối tượng được cáp quyền.', noObservation: 'Chưa có dữ liệu đo.',
    source: 'Nguồn', recordedAt: 'Thời điểm', quality: 'Chất lượng', verification: 'Xác minh',
    noSensorTitle: 'Chưa kết nối cảm biến', noSensor: 'Không có dữ liệu cảm biến.',
    aiUnavailableTitle: 'AI chưa kết nối', aiUnavailable: 'Chưa có dịch vụ AI.',
    scienceUnavailableTitle: 'Thư viện chưa sẵn sàng', scienceUnavailable: 'Chưa có dữ liệu thư viện.',
    missionNote: 'Chỉ hiển thị đối tượng được cấp quyền.',
    role: 'Vai trò', allowedSubjects: 'Đối tượng được cấp quyền',
    settingsTitle: 'Cài đặt', connectionTitle: 'Server', accountTitle: 'Tài khoản', sessionExpiry: 'Phiên hết hạn',
    saved: 'Đã lưu', networkError: 'Không thể kết nối. Kiểm tra địa chỉ server và mạng.', unauthorized: 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn.', forbidden: 'Tài khoản không có quyền xem dữ liệu này.', notFound: 'Server chưa có dữ liệu hoặc chức năng này.', serverError: 'Server gặp lỗi. Thử lại sau.',
    statusReady: 'Có dữ liệu mới', statusStale: 'Dữ liệu đã cũ', statusNoData: 'Chưa có dữ liệu', statusOffline: 'Ngoại tuyến', statusDenied: 'Không được cấp quyền', statusError: 'Lỗi dữ liệu', statusUnverified: 'Chưa xác minh', statusOther: 'Trạng thái khác',
    privacy: 'Ứng dụng native lưu phiên trong vùng bảo mật của thiết bị; bản web chỉ lưu trong phiên trình duyệt hiện tại. Ứng dụng không lưu mật khẩu.',
    back: 'Quay lại', save: 'Lưu địa chỉ', signInKicker: 'TRUY CẬP AN TOÀN',
    connectionHint: 'Android emulator: http://10.0.2.2:8765. USB: adb reverse tcp:8765 tcp:8765.',
    settingsConnectionHint: 'Địa chỉ chỉ lưu trên thiết bị. Đăng nhập dùng một token phiên riêng.',
    aiFlowDescription: 'Khi server tích hợp AI, app sẽ gửi yêu cầu đã xác thực và hiển thị nguồn, trạng thái cùng phản hồi rõ ràng.',
    scienceKicker: 'THƯ VIỆN CÓ NGUỒN', scienceRulesTitle: 'Nguyên tắc hiển thị',
    scienceRulesBody: 'Giữ nguyên nội dung gốc, đường dẫn, trang, trích dẫn và thông tin quyền sử dụng. Bản dịch phải tách riêng và ghi trạng thái rà soát.',
    moreTitle: 'Thêm', notifications: 'Thông báo', notificationsUnavailable: 'Chưa có nguồn thông báo trên máy chủ.',
    helpTitle: 'Trợ giúp', helpUnavailable: 'Máy chủ chưa cung cấp dịch vụ hỗ trợ trong ứng dụng.',
    privacyTitle: 'Quyền riêng tư', privacyAi: 'Tin nhắn AI được gửi đến máy chủ và mô hình đã chọn. Gửi đến AI đám mây cần có xác nhận riêng.',
    privacyDemo: 'Demo NASA dùng dữ liệu lịch sử công khai. Đây không phải hồ sơ y tế hiện tại.',
    serverUnknown: 'Chưa kiểm tra', connectionCheck: 'Kiểm tra kết nối',
    careTitle: 'Hành trình chăm sóc', careSubject: 'Hồ sơ', careNew: 'Bắt đầu hành trình', careEpisodes: 'Hành trình đã lưu', careNoEpisodes: 'Chưa có hành trình.',
    careConcern: 'Điều bạn muốn ghi nhận', careConcernPlaceholder: 'Nhập nội dung tự khai', careSymptoms: 'Triệu chứng', careSymptomsPlaceholder: 'Phân cách bằng dấu phẩy', careSymptomsInvalid: 'Tối đa 20 triệu chứng; mỗi mục không quá 120 ký tự.', careConsent: 'Tôi đồng ý lưu lời khai này vào hồ sơ đã chọn.', careStart: 'Lưu lời khai',
    careNotAssessed: 'Chưa được đánh giá y khoa', careUserReported: 'Thông tin do người dùng tự khai; không phải chẩn đoán.', careGather: 'Thu thập', careEvaluate: 'Đánh giá', careAct: 'Hành động', careRecheck: 'Kiểm tra lại', careClosed: 'Đã đóng',
    careGatherSummary: 'Tóm tắt thông tin thu thập', careActionSummary: 'Hành động đã chọn', careRecheckSummary: 'Kết quả kiểm tra lại', careNextSummary: 'Ghi chú bước tiếp theo', careSummaryPlaceholder: 'Ghi nội dung do bạn xác nhận', careActionStatus: 'Trạng thái hành động', careDone: 'Đã thực hiện', careNotDone: 'Chưa thực hiện', careCannotDo: 'Không thể thực hiện', careOutcome: 'Kết quả', careBetter: 'Tốt hơn', careUnchanged: 'Không đổi', careWorse: 'Xấu hơn', careUnknown: 'Không rõ', careAfterRecheck: 'Tiếp theo', careContinue: 'Tiếp tục', careClose: 'Đóng hành trình', careConfirm: 'Tôi xác nhận nội dung và bước tiếp theo.', careHistory: 'Lịch sử', careHumanConfirmed: 'Người dùng xác nhận', careUnverified: 'Chưa xác minh', careDataReady: 'Có dữ liệu', careDataNoData: 'Chưa có dữ liệu', careDataStale: 'Dữ liệu cũ', careDataOffline: 'Ngoại tuyến', careDataDenied: 'Không được cấp quyền', careDataError: 'Lỗi dữ liệu', careDataOther: 'Trạng thái khác', careUnavailable: 'Không tìm thấy hành trình.', careConflict: 'Hành trình đã đổi. Tải lại để tiếp tục.', careInvalid: 'Thông tin không hợp lệ.',
    demoTitle: 'Demo NASA', demoKicker: 'DỮ LIỆU NASA', demoBannerTitle: 'Dữ liệu chuyến bay Mercury', demoOpen: 'Mở demo', demoIntroTitle: 'Chuyến bay Mercury-Atlas 7', demoHistorical: 'Dữ liệu lịch sử', demoPublisher: 'Đơn vị', demoPublished: 'Ngày công bố', demoTimepoints: 'Mốc thời gian', demoMetrics: 'Chỉ số', demoReportedValues: 'Giá trị đã công bố', demoOpenNasaSource: 'Mở tài liệu NASA', demoOpenChallenge: 'Mở đề bài', demoLimitations: 'Giới hạn dữ liệu', demoHistoricalLimit: 'Dữ liệu lấy từ báo cáo sau chuyến bay năm 1962; không phải dữ liệu trực tiếp hoặc hồ sơ y tế hiện tại.', demoUnavailableTitle: 'Không có trong nguồn', demoLoadData: 'Mở dữ liệu', demoSourceError: 'Không đọc được dữ liệu nguồn', demoUnavailableEcg: 'Dạng sóng ECG', demoUnavailableSpo2: 'SpO₂', demoUnavailableSleep: 'Giấc ngủ', demoUnavailableMood: 'Tâm trạng', demoUnavailableGlucose: 'Đường huyết', demoUnavailableRadiation: 'Liều bức xạ cá nhân', demoUnavailableContinuousEcg: 'ECG liên tục', demoUnavailableLongitudinal: 'Luồng cảm biến dài hạn', demoUnavailableOther: 'Chỉ số khác', demoSourceTable: 'Bảng nguồn', demoRange: 'Khoảng', demoSamples: 'Số mẫu', demoMissingNotReported: 'Nguồn không công bố', demoMissingNotObtained: 'Không thu được', demoValueUnavailable: 'Không có giá trị', demoQualifierReported: 'Giá trị báo cáo', demoQualifierPhaseMean: 'Trung bình theo giai đoạn', demoQualifierInstrumentCaveated: 'Phân loại thiết bị có lưu ý', demoQualifierSourceTabulated: 'Giá trị trong bảng nguồn', demoQualifierReportedCombined: 'Giá trị tổng hợp được báo cáo', demoQualifierReportedRange: 'Khoảng được báo cáo', demoQualifierOther: 'Lưu ý theo nguồn',
    aiChecking: 'Đang kiểm tra AI', aiPromptPlaceholder: 'Nhập câu hỏi', aiSend: 'Gửi', aiSending: 'Đang gửi', aiLocal: 'AI cục bộ', aiCloud: 'AI đám mây', aiCloudConsent: 'Cho phép gửi nội dung cuộc trò chuyện đến AI đám mây.', aiCloudConsentRequired: 'Cần xác nhận trước khi gửi đến AI đám mây.', aiRequestUnavailable: 'Yêu cầu AI hiện không khả dụng.', aiNoSources: 'Không có nguồn được trả về.',
    scienceSearchPlaceholder: 'Tìm trong thư viện', scienceSearch: 'Tìm', scienceNoResults: 'Không tìm thấy tài liệu.', scienceArticleCount: 'Tài liệu', scienceCategory: 'Danh mục', scienceSections: 'Nội dung', scienceReferences: 'Tài liệu tham khảo', scienceTables: 'Bảng', scienceBack: 'Quay lại thư viện', scienceSourceStatus: 'Trạng thái nguồn', sciencePublisher: 'Đơn vị xuất bản', scienceOriginalLink: 'Tài liệu gốc', scienceRetrievedAt: 'Ngày truy xuất', scienceLicense: 'Giấy phép', scienceAttribution: 'Ghi công', scienceSha256: 'SHA-256', scienceSourceNote: 'Cờ xác minh trong JSON là dữ liệu khai báo, không phải xác minh độc lập byte PDF gốc.', sciencePage: 'Trang', scienceRecordUnavailable: 'Không có bản ghi này.', sciencePdfNotVerified: 'Chưa xác minh PDF gốc.', scienceRulesNotValidated: 'Quy tắc lâm sàng chưa được xác nhận.',
    authorized: 'Đã cấp quyền',
  },
  en: {
    brand: 'AETHERION', tagline: 'One Health. One Humanity. Beyond Earth.',
    portalEyebrow: 'AETHERION HEALTH', portalTitle: 'Health portal', portalDescription: 'Choose a space to continue. Health data stays behind sign-in.',
    personal: 'Health', personalDesc: 'Profile and data recorded by the server.',
    monitor: 'Monitor', monitorDesc: 'Review data, its source, and when it was recorded.',
    ai: 'AI', aiDesc: 'The assistant works only when the server provides an AI service.',
    science: 'Library', scienceDesc: 'Scientific material with sources and verification status.',
    mission: 'Crew', missionDesc: 'A workspace for users with the required access.',
    signIn: 'Sign in', signOut: 'Sign out', signInTitle: 'Connect to AETHERION', signInSubtitle: 'Use an account created on the AETHERION Server.',
    serverUrl: 'Server URL', username: 'Username', password: 'Password', connect: 'Check connection', connecting: 'Connecting…', signInAction: 'Sign in', signingIn: 'Signing in…', cancel: 'Back',
    urlRequired: 'Enter a server address first.', urlInvalid: 'The server address is invalid.', urlLocalhost: 'A physical phone needs the server computer’s LAN address, not localhost.', urlSaved: 'Server address saved on this device.',
    loginRequired: 'Sign in to open protected data.', loginFailed: 'Sign-in failed. Check the account, password, and server.', serverOnline: 'Server responded', serverOffline: 'Server not connected',
    home: 'Home', settings: 'Settings', language: 'Language', vietnamese: 'Tiếng Việt', english: 'English', notSignedIn: 'Not signed in',
    healthTitle: 'Health', monitorTitle: 'Monitoring', missionTitle: 'Crew',
    loading: 'Loading data…', refresh: 'Refresh', noData: 'No data yet', noDataNote: 'No records. Health status is unknown.',
    availability: 'Data status', observations: 'Observations', latest: 'Latest record', metrics: 'Recorded metrics',
    subject: 'Data subject', noSubject: 'No authorized subject.', noObservation: 'No readings.',
    source: 'Source', recordedAt: 'Recorded at', quality: 'Quality', verification: 'Verification',
    noSensorTitle: 'No sensor connected', noSensor: 'No sensor data.',
    aiUnavailableTitle: 'AI unavailable', aiUnavailable: 'No AI service available.',
    scienceUnavailableTitle: 'Library unavailable', scienceUnavailable: 'Library data unavailable.',
    missionNote: 'Authorized crew only.',
    role: 'Role', allowedSubjects: 'Authorized subjects',
    settingsTitle: 'Settings', connectionTitle: 'Server', accountTitle: 'Account', sessionExpiry: 'Session expires',
    saved: 'Saved', networkError: 'Could not connect. Check the server address and network.', unauthorized: 'The session is invalid or expired.', forbidden: 'This account cannot access this data.', notFound: 'The server does not have this data or feature yet.', serverError: 'The server encountered an error. Try again later.',
    statusReady: 'Current data available', statusStale: 'Data is stale', statusNoData: 'No data yet', statusOffline: 'Offline', statusDenied: 'Access denied', statusError: 'Data error', statusUnverified: 'Unverified', statusOther: 'Other status',
    privacy: 'The native app stores the session in device-protected storage; web keeps it only for the current browser session. The app does not save your password.',
    back: 'Back', save: 'Save address', signInKicker: 'SECURE ACCESS',
    connectionHint: 'Android emulator: http://10.0.2.2:8765. USB: adb reverse tcp:8765 tcp:8765.',
    settingsConnectionHint: 'The address is stored on this device. Sign-in uses a separate session token.',
    aiFlowDescription: 'When the server integrates AI, the app will send authenticated requests and clearly display sources, status, and responses.',
    scienceKicker: 'SOURCE-ANCHORED LIBRARY', scienceRulesTitle: 'Display rule',
    scienceRulesBody: 'Preserve original text, links, page anchors, citations, and rights metadata. Translations stay separate and carry their review status.',
    moreTitle: 'More', notifications: 'Notifications', notificationsUnavailable: 'No notification feed is available from the server.',
    helpTitle: 'Help', helpUnavailable: 'The server does not provide in-app support yet.',
    privacyTitle: 'Privacy', privacyAi: 'AI messages are sent to the server and selected model. Sending to cloud AI requires separate consent.',
    privacyDemo: 'The NASA demo uses public historical data. It is not a current medical record.',
    serverUnknown: 'Not checked', connectionCheck: 'Check connection',
    careTitle: 'Care Journey', careSubject: 'Profile', careNew: 'Start a journey', careEpisodes: 'Saved journeys', careNoEpisodes: 'No journeys yet.',
    careConcern: 'What you want to record', careConcernPlaceholder: 'Enter a self-report', careSymptoms: 'Symptoms', careSymptomsPlaceholder: 'Separate items with commas', careSymptomsInvalid: 'Use up to 20 symptoms, each 120 characters or fewer.', careConsent: 'I agree to save this self-report to the selected profile.', careStart: 'Save report',
    careNotAssessed: 'Not clinically assessed', careUserReported: 'User-reported information; not a diagnosis.', careGather: 'Gather', careEvaluate: 'Evaluate', careAct: 'Act', careRecheck: 'Recheck', careClosed: 'Closed',
    careGatherSummary: 'Gathered information', careActionSummary: 'Action selected', careRecheckSummary: 'Recheck result', careNextSummary: 'Next-step note', careSummaryPlaceholder: 'Enter information you confirm', careActionStatus: 'Action status', careDone: 'Done', careNotDone: 'Not done', careCannotDo: 'Cannot do', careOutcome: 'Outcome', careBetter: 'Better', careUnchanged: 'Unchanged', careWorse: 'Worse', careUnknown: 'Unknown', careAfterRecheck: 'Next step', careContinue: 'Continue', careClose: 'Close journey', careConfirm: 'I confirm this information and next step.', careHistory: 'History', careHumanConfirmed: 'User confirmed', careUnverified: 'Unverified', careDataReady: 'Data available', careDataNoData: 'No data', careDataStale: 'Stale data', careDataOffline: 'Offline', careDataDenied: 'Access denied', careDataError: 'Data error', careDataOther: 'Other status', careUnavailable: 'Journey not found.', careConflict: 'The journey changed. Refresh to continue.', careInvalid: 'The information is invalid.',
    demoTitle: 'NASA Demo', demoKicker: 'NASA DATA', demoBannerTitle: 'Mercury flight data', demoOpen: 'Open demo', demoIntroTitle: 'Mercury-Atlas 7 flight', demoHistorical: 'Historical data', demoPublisher: 'Publisher', demoPublished: 'Published', demoTimepoints: 'Timepoints', demoMetrics: 'Metrics', demoReportedValues: 'Reported values', demoOpenNasaSource: 'Open NASA report', demoOpenChallenge: 'Open challenge', demoLimitations: 'Data limits', demoHistoricalLimit: 'These data come from a 1962 postflight report. They are not live data or a current medical record.', demoUnavailableTitle: 'Not in source', demoLoadData: 'Open data', demoSourceError: 'Source data could not be read', demoUnavailableEcg: 'ECG waveform', demoUnavailableSpo2: 'SpO₂', demoUnavailableSleep: 'Sleep', demoUnavailableMood: 'Mood', demoUnavailableGlucose: 'Blood glucose', demoUnavailableRadiation: 'Personal radiation dose', demoUnavailableContinuousEcg: 'Continuous ECG', demoUnavailableLongitudinal: 'Longitudinal sensor stream', demoUnavailableOther: 'Other metric', demoSourceTable: 'Source table', demoRange: 'Range', demoSamples: 'Samples', demoMissingNotReported: 'Not reported by source', demoMissingNotObtained: 'Not obtained', demoValueUnavailable: 'No value', demoQualifierReported: 'Reported value', demoQualifierPhaseMean: 'Phase mean', demoQualifierInstrumentCaveated: 'Instrument category with caveat', demoQualifierSourceTabulated: 'Tabulated in source', demoQualifierReportedCombined: 'Reported combined value', demoQualifierReportedRange: 'Reported range', demoQualifierOther: 'Source qualifier',
    aiChecking: 'Checking AI', aiPromptPlaceholder: 'Ask a question', aiSend: 'Send', aiSending: 'Sending', aiLocal: 'Local AI', aiCloud: 'Cloud AI', aiCloudConsent: 'Allow this conversation to be sent to cloud AI.', aiCloudConsentRequired: 'Consent is required before sending to cloud AI.', aiRequestUnavailable: 'AI request is unavailable.', aiNoSources: 'No sources were returned.',
    scienceSearchPlaceholder: 'Search the library', scienceSearch: 'Search', scienceNoResults: 'No articles found.', scienceArticleCount: 'Articles', scienceCategory: 'Category', scienceSections: 'Sections', scienceReferences: 'References', scienceTables: 'Tables', scienceBack: 'Back to library', scienceSourceStatus: 'Source status', sciencePublisher: 'Publisher', scienceOriginalLink: 'Original source', scienceRetrievedAt: 'Retrieved', scienceLicense: 'License', scienceAttribution: 'Attribution', scienceSha256: 'SHA-256', scienceSourceNote: 'A verification flag in JSON is a claim, not independent verification of the original PDF bytes.', sciencePage: 'Page', scienceRecordUnavailable: 'This record is unavailable.', sciencePdfNotVerified: 'Original PDF not verified.', scienceRulesNotValidated: 'Clinical rules are not validated.',
    authorized: 'Authorized',
  },
} as const;

export type MessageKey = keyof typeof messages.vi;
export function t(locale: Locale, key: MessageKey): string {
  return messages[locale][key] ?? messages.en[key];
}

export async function loadLocale(): Promise<Locale> {
  try {
    const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
    const value = await AsyncStorage.getItem('aetherion.mobile.locale.v1');
    return value === 'vi' ? 'vi' : 'en';
  } catch {
    return 'en';
  }
}

export async function saveLocale(locale: Locale): Promise<void> {
  const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
  await AsyncStorage.setItem('aetherion.mobile.locale.v1', locale);
}
