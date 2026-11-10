import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Phong Hỏa · Duyệt bản nháp",
  description: "Bản xem thử hàng đợi bản nháp CTI ngoại tuyến",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
