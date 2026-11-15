import { Locale } from './types';
const en = {
  demo: 'Demo', welcome: 'Welcome back', tagline: 'Your health. One connected space.',
  connection: 'Server connection', appearance: 'Appearance', theme: 'Theme', mode: 'Mode', system: 'System', light: 'Light', dark: 'Dark',
  amethyst: 'Amethyst', ocean: 'Ocean', sunset: 'Sunset', forest: 'Forest', midnight: 'Midnight', sand: 'Sand', rose: 'Rose', gold: 'Gold',
  accentColor: 'Accent color', accentPurple: 'Purple', accentTeal: 'Teal', accentOrange: 'Orange', accentBlack: 'Charcoal', accentRose: 'Rose', accentBlue: 'Blue', accentGold: 'Gold',
  textColor: 'Text color', textTheme: 'Match theme', textGraphite: 'Graphite', textNavy: 'Navy', textPlum: 'Plum', textWarm: 'Warm', motion: 'Reduce motion',
  profile: 'Profile', chooseProfile: 'Choose a profile', noProfiles: 'No profiles assigned', retry: 'Try again', continueAs: 'Continue as',
  registerProfile: 'Create profile', profileName: 'Display name', profileId: 'Profile ID', serverSaved: 'Server saved',
  demoStart: 'Explore data', demoCaption: 'NASA MA-7 · 1962', demoSummary: '19 timepoints · 18 metrics · 83 reported values',
  sourceDetails: 'Source details', archive: 'Flight archive', phases: 'Flight phases', clinical: 'Clinical exams', blood: 'Blood count', pressure: 'Blood pressure',
  noLive: 'Historical archive', serverArchive: 'Server archive', bundledArchive: 'On-device archive', records: 'Records', details: 'Details', backToLogin: 'Back to sign in', page: 'Page', next: 'Next', previous: 'Previous',
  loadMore: 'Load more', signOut: 'Sign out', noMatch: 'No matching records', selected: 'Selected', sensorUnknown: 'Sensor status unavailable', aiServerSettings: 'AI provider',
  teamLogo: 'Truy Tinh logo', serverData: 'Server data', nasaLibrary: 'NASA CliFF', missingSources: 'Missing source',
  notAvailable: 'Unavailable', localReady: 'Local ready', localUnavailable: 'Local unavailable',
  cloudReady: 'Cloud ready', cloudUnavailable: 'Cloud unavailable', sourceLimitations: 'Source limits',
  healthGuide: 'Health guide', healthGuideIntro: 'Understand the measures you see.', healthGuideNote: 'These notes explain common measurements. They do not set mission limits or diagnose. Follow the flight medical protocol and tell the medical officer about symptoms or unexpected readings.',
  healthTipTitle: 'A quick health tip', healthTipBody: 'A reading needs its time, unit, and context. One number alone cannot tell you what is wrong.', healthTipOpen: 'View guide', healthTipDismiss: 'Got it', healthTipClose: 'Close tip',
  guideMeasures: 'What it measures', guidePurpose: 'Why it is tracked', guideTip: 'Use it well', guideSources: 'Sources', guideOpenSource: 'Open source',
};
const vi: Record<keyof typeof en, string> = {
  demo: 'Demo', welcome: 'Chào mừng trở lại', tagline: 'Sức khỏe của bạn. Một không gian kết nối.',
  connection: 'Kết nối máy chủ', appearance: 'Giao diện', theme: 'Chủ đề', mode: 'Chế độ', system: 'Hệ thống', light: 'Sáng', dark: 'Tối',
  amethyst: 'Thạch anh tím', ocean: 'Đại dương', sunset: 'Hoàng hôn', forest: 'Rừng xanh', midnight: 'Đêm sâu', sand: 'Cát ấm', rose: 'Hồng', gold: 'Vàng ấm',
  accentColor: 'Màu nhấn', accentPurple: 'Tím', accentTeal: 'Xanh ngọc', accentOrange: 'Cam', accentBlack: 'Than chì', accentRose: 'Hồng', accentBlue: 'Xanh dương', accentGold: 'Vàng',
  textColor: 'Màu chữ', textTheme: 'Theo giao diện', textGraphite: 'Than chì', textNavy: 'Xanh navy', textPlum: 'Tím mận', textWarm: 'Nâu ấm', motion: 'Giảm chuyển động',
  profile: 'Hồ sơ', chooseProfile: 'Chọn hồ sơ', noProfiles: 'Chưa được cấp hồ sơ', retry: 'Thử lại', continueAs: 'Tiếp tục với',
  registerProfile: 'Tạo hồ sơ', profileName: 'Tên hiển thị', profileId: 'Mã hồ sơ', serverSaved: 'Đã lưu máy chủ',
  demoStart: 'Khám phá dữ liệu', demoCaption: 'NASA MA-7 · 1962', demoSummary: '19 mốc · 18 chỉ số · 83 giá trị được ghi nhận',
  sourceDetails: 'Chi tiết nguồn', archive: 'Kho chuyến bay', phases: 'Giai đoạn bay', clinical: 'Khám lâm sàng', blood: 'Công thức máu', pressure: 'Huyết áp',
  noLive: 'Dữ liệu lịch sử', serverArchive: 'Dữ liệu máy chủ', bundledArchive: 'Dữ liệu trên máy', records: 'Bản ghi', details: 'Chi tiết', backToLogin: 'Về đăng nhập', page: 'Trang', next: 'Tiếp', previous: 'Trước',
  loadMore: 'Tải thêm', signOut: 'Đăng xuất', noMatch: 'Không có bản ghi phù hợp', selected: 'Đã chọn', sensorUnknown: 'Chưa xác định trạng thái cảm biến', aiServerSettings: 'Nhà cung cấp AI',
  teamLogo: 'Logo Truy Tinh', serverData: 'Dữ liệu máy chủ', nasaLibrary: 'NASA CliFF', missingSources: 'Nguồn còn thiếu',
  notAvailable: 'Chưa có dữ liệu', localReady: 'AI cục bộ sẵn sàng', localUnavailable: 'AI cục bộ chưa sẵn sàng',
  cloudReady: 'AI đám mây sẵn sàng', cloudUnavailable: 'AI đám mây chưa sẵn sàng', sourceLimitations: 'Giới hạn nguồn',
  healthGuide: 'Cẩm nang chỉ số', healthGuideIntro: 'Hiểu các chỉ số bạn nhìn thấy.', healthGuideNote: 'Các ghi chú giải thích phép đo thường gặp; không đặt ngưỡng riêng cho nhiệm vụ và không chẩn đoán. Làm theo quy trình y tế chuyến bay, báo nhân viên y tế khi có triệu chứng hoặc kết quả bất thường.',
  healthTipTitle: 'Mẹo sức khỏe', healthTipBody: 'Mỗi kết quả cần có thời điểm, đơn vị và bối cảnh. Một con số riêng lẻ không cho biết nguyên nhân.', healthTipOpen: 'Xem hướng dẫn', healthTipDismiss: 'Đã rõ', healthTipClose: 'Đóng mẹo',
  guideMeasures: 'Chỉ số đo gì', guidePurpose: 'Theo dõi để làm gì', guideTip: 'Cách ghi nhận', guideSources: 'Nguồn', guideOpenSource: 'Mở nguồn',
};
export function copy(locale: Locale, key: keyof typeof en) { return (locale === 'vi' ? vi : en)[key]; }


