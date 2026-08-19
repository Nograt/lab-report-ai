"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { Logo } from "@/components/ui/Logo";

const navigation = [
  {
    label: "Nowe sprawozdanie",
    href: "/reports/new",
  },
  {
    label: "Przedmioty",
    href: "/settings/subjects",
  },
  {
    label: "Profil",
    href: "/settings/profile",
  },
];

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  function isActive(href: string) {
    return pathname === href;
  }

  return (
    <header className="sticky top-0 z-50 border-b border-neutral-200 bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link
          href="/"
          aria-label="Sprawko - strona główna"
          onClick={() => setIsOpen(false)}
        >
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`
                rounded-lg px-3 py-2 text-sm font-medium
                ${
                  isActive(item.href)
                    ? "bg-orange-50 text-orange-600"
                    : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950"
                }
              `}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <button
          type="button"
          onClick={() => setIsOpen((current) => !current)}
          className="
            flex size-10 items-center justify-center
            rounded-lg text-neutral-700
            hover:bg-neutral-100
            md:hidden
          "
          aria-label={isOpen ? "Zamknij menu" : "Otwórz menu"}
          aria-expanded={isOpen}
        >
          {isOpen ? (
            <svg
              viewBox="0 0 24 24"
              fill="none"
              className="size-5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            >
              <path d="M6 6L18 18" />
              <path d="M18 6L6 18" />
            </svg>
          ) : (
            <svg
              viewBox="0 0 24 24"
              fill="none"
              className="size-5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            >
              <path d="M4 7H20" />
              <path d="M4 12H20" />
              <path d="M4 17H20" />
            </svg>
          )}
        </button>
      </div>

      {isOpen && (
        <nav className="border-t border-neutral-200 bg-white px-6 py-3 md:hidden">
          <div className="mx-auto flex max-w-7xl flex-col gap-1">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={`
                  rounded-lg px-3 py-3 text-sm font-medium
                  ${
                    isActive(item.href)
                      ? "bg-orange-50 text-orange-600"
                      : "text-neutral-700 hover:bg-neutral-50"
                  }
                `}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}