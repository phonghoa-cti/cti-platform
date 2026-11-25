import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Phong Hỏa · Duyệt bản nháp",
  description: "Hàng đợi duyệt bản nháp CTI Phong Hỏa",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
