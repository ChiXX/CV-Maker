'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { label: 'Home', href: '/' },
    { label: 'Generation', href: '/wizard' },
    { label: 'Applications', href: '/applications' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex justify-center p-4">
      <div className="flex items-center gap-1 p-1 bg-white/70 dark:bg-zinc-900/70 backdrop-blur-xl border border-white/20 dark:border-zinc-800/50 rounded-2xl shadow-2xl shadow-black/5 ring-1 ring-black/5">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`px-4 py-2 text-sm font-medium transition-all duration-300 rounded-xl ${
                isActive
                  ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-lg'
                  : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50 hover:text-zinc-900 dark:hover:text-white'
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
