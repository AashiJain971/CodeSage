// /Users/adityajain/CodeSageIITD/frontend/app/layout.jsx
import './globals.css';

export const metadata = {
  title: 'CodeSage - AI Interview System',
  description: 'Intelligent interview system with AI-powered voice interactions',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div id="root">
          {children}
        </div>
      </body>
    </html>
  );
}