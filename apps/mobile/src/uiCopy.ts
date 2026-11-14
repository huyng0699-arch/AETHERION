import { Locale } from './types';
const en = {
  demo: 'Demo', demoHint: 'Explore the NASA flight archive', welcome: 'Welcome back', tagline: 'Your health. One connected space.',
  connection: 'Server connection', appearance: 'Appearance', theme: 'Theme', mode: 'Mode', system: 'System', light: 'Light', dark: 'Dark',
  amethyst: 'Amethyst', ocean: 'Ocean', rose: 'Rose', midnight: 'Midnight', motion: 'Reduce motion',
  profile: 'Profile', chooseProfile: 'Choose a profile', noProfiles: 'No profiles assigned', retry: 'Try again', continueAs: 'Continue as',
  registerProfile: 'Create profile', profileName: 'Display name', profileId: 'Profile ID', serverSaved: 'Server saved',
  demoStart: 'Explore data', demoCaption: 'NASA MA-7 · 1962', demoSummary: '19 timepoints · 18 metrics · 83 reported values',
  sourceDetails: 'Source details', archive: 'Flight archive', phases: 'Flight phases', clinical: 'Clinical exams', blood: 'Blood count', pressure: 'Blood pressure',
  noLive: 'Historical archive', records: 'Records', details: 'Details', backToLogin: 'Back to sign in', page: 'Page', next: 'Next', previous: 'Previous',
  loadMore: 'Load more', signOut: 'Sign out', noMatch: 'No matching records', selected: 'Selected',
};
const vi: Record<keyof typeof en, string> = {
  demo: 'Demo', demoHint: 'Khám phá dữ liệu chuyến bay NASA', welcome: 'Chào mừng trở lại', tagline: 'Sức khỏe của bạn. Một không gian kết nối.',
  connection: 'Kết nối máy chủ', appearance: 'Giao diện', theme: 'Chủ đề', mode: 'Chế độ', system: 'Hệ thống', light: 'Sáng', dark: 'Tối',
  amethyst: 'Thạch anh tím', ocean: 'Đại dương', rose: 'Hoa hồng', midnight: 'Đêm sâu', motion: 'Giảm chuyển động',
  profile: 'Hồ sơ', chooseProfile: 'Chọn hồ sơ', noProfiles: 'Chưa được cấp hồ sơ', retry: 'Thử lại', continueAs: 'Tiếp tục với',
  registerProfile: 'Tạo hồ sơ', profileName: 'Tên hiển thị', profileId: 'Mã hồ sơ', serverSaved: 'Đã lưu máy chủ',
  demoStart: 'Khám phá dữ liệu', demoCaption: 'NASA MA-7 · 1962', demoSummary: '19 mốc · 18 chỉ số · 83 giá trị được ghi nhận',
  sourceDetails: 'Chi tiết nguồn', archive: 'Kho chuyến bay', phases: 'Giai đoạn bay', clinical: 'Khám lâm sàng', blood: 'Công thức máu', pressure: 'Huyết áp',
  noLive: 'Dữ liệu lịch sử', records: 'Bản ghi', details: 'Chi tiết', backToLogin: 'Về đăng nhập', page: 'Trang', next: 'Tiếp', previous: 'Trước',
  loadMore: 'Tải thêm', signOut: 'Đăng xuất', noMatch: 'Không có bản ghi phù hợp', selected: 'Đã chọn',
};
export function copy(locale: Locale, key: keyof typeof en) { return (locale === 'vi' ? vi : en)[key]; }
