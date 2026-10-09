'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  PawPrint,
  Heart,
  User,
  LogOut,
  LayoutDashboard,
  Shield,
  Bell,
  CheckCheck,
  ChevronDown,
  BookOpen,
  ClipboardList,
  Stethoscope,
  PawPrint as AnimalsIcon,
  Building2,
  Megaphone,
  HandCoins,
  Newspaper,
  Settings,
  BadgeCheck,
  ShieldAlert,
  CreditCard,
  BarChart3,
  BookText,
  ClipboardCheck,
  HeartHandshake,
  Gift,
  BellRing,
} from 'lucide-react';

import { useAuthStore } from '@/lib/stores/authStore';
import { useNotificationStore } from '@/lib/stores/notificationStore';
import { ROUTES } from '@/lib/constants';
import type { UserRole } from '@/lib/types';
import LocaleSwitcher from './LocaleSwitcher';
import ThemeToggle from './ThemeToggle';
import DropdownMenu, { DropdownDivider } from '@/components/ui/DropdownMenu';

type PanelItem = { label: string; href: string; icon: React.ReactNode };

type RolePanelConfig = {
  label: string;
  color: { text: string; hover: string };
  icon: React.ReactNode;
  items: PanelItem[];
};

type AccountItem = { label: string; href: string; icon: React.ReactNode };

export default function Header() {
  const [mobileState, setMobileState] = useState<'closed' | 'open' | 'closing'>('closed');
  const closeMobile = () => setMobileState('closing');
  const pathname = usePathname();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isAuthReady = useAuthStore((s) => s.isAuthReady);
  const user = useAuthStore((s) => s.user);
  const signOut = useAuthStore((s) => s.signOut);
  const t = useTranslations('nav');
  const tCommon = useTranslations('common');
  const tManual = useTranslations('manual');
  const tNotif = useTranslations('notifications');

  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const notifications = useNotificationStore((s) => s.notifications);
  const fetchUnreadCount = useNotificationStore((s) => s.fetchUnreadCount);
  const fetchNotifications = useNotificationStore((s) => s.fetchNotifications);
  const markAllAsRead = useNotificationStore((s) => s.markAllAsRead);

  useEffect(() => {
    if (!isAuthenticated) return;
    void fetchUnreadCount();
    const interval = setInterval(() => void fetchUnreadCount(), 30000);
    return () => clearInterval(interval);
  }, [isAuthenticated, fetchUnreadCount]);

  const publicNav = [
    { label: t('animals'), href: ROUTES.ANIMALS },
    { label: t('shelters'), href: ROUTES.SHELTERS },
    { label: t('campaigns'), href: ROUTES.CAMPAIGNS },
    { label: t('lookingToAdopt'), href: ROUTES.LOOKING_TO_ADOPT },
    { label: t('supportPlatform'), href: ROUTES.PLATFORM_SUPPORT },
    { label: t('blog'), href: ROUTES.BLOG },
  ];

  const aboutSubLinks = [
    { label: t('aboutUs'), href: ROUTES.ABOUT },
    { label: t('workWithUs'), href: ROUTES.WORK_WITH_US },
    { label: t('strategicAllies'), href: ROUTES.STRATEGIC_ALLIES },
  ];

  const pathnameWithoutLocale = (pathname ?? '/').replace(/^\/[a-z]{2}(?=\/|$)/, '') || '/';
  const isActive = (href: string) =>
    href === '/'
      ? pathnameWithoutLocale === '/'
      : pathnameWithoutLocale === href || pathnameWithoutLocale.startsWith(href + '/');
  const isAboutActive = aboutSubLinks.some((link) => isActive(link.href));

  const rolePanel = buildRolePanel(user?.role, t);
  const accountItems: AccountItem[] = [
    { label: t('myProfile'), href: ROUTES.MY_PROFILE, icon: <User className="h-4 w-4" /> },
    { label: t('favorites'), href: ROUTES.FAVORITES, icon: <Heart className="h-4 w-4" /> },
    { label: t('myApplications'), href: ROUTES.MY_APPLICATIONS, icon: <ClipboardCheck className="h-4 w-4" /> },
    { label: t('myDonations'), href: ROUTES.MY_DONATIONS, icon: <Gift className="h-4 w-4" /> },
    { label: t('mySponsorships'), href: ROUTES.MY_SPONSORSHIPS, icon: <HeartHandshake className="h-4 w-4" /> },
    { label: t('myNotifications'), href: ROUTES.MY_NOTIFICATIONS, icon: <BellRing className="h-4 w-4" /> },
  ];

  const notificationContent = ({ close }: { close: () => void }) => (
    <>
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-tertiary">
        <span className="text-sm font-semibold text-text-primary">{tNotif('bellTitle')}</span>
        {unreadCount > 0 && (
          <button
            type="button"
            onClick={() => void markAllAsRead()}
            className="flex items-center gap-1 text-xs text-teal-600 hover:text-teal-700"
          >
            <CheckCheck className="h-3 w-3" />
            {tNotif('markAllRead')}
          </button>
        )}
      </div>
      <div className="max-h-72 overflow-y-auto">
        {notifications.length === 0 ? (
          <p className="px-4 py-6 text-sm text-text-quaternary text-center">{tNotif('noNotifications')}</p>
        ) : (
          notifications.slice(0, 10).map((n) => (
            <div
              key={n.id}
              className={`px-4 py-3 border-b border-border-tertiary text-sm ${
                n.is_read ? 'text-text-quaternary' : 'text-text-secondary bg-teal-50/30'
              }`}
            >
              <p className="font-medium">{tNotif(`events.${n.event_key}`)}</p>
              <p className="text-xs text-text-quaternary mt-0.5">{new Date(n.created_at).toLocaleString()}</p>
            </div>
          ))
        )}
      </div>
      <Link
        href={ROUTES.MY_NOTIFICATIONS}
        role="menuitem"
        className="block px-4 py-2.5 text-xs text-center text-teal-600 hover:bg-surface-hover border-t border-border-tertiary"
        onClick={close}
      >
        {tNotif('viewAllNotifications')}
      </Link>
    </>
  );

  const accountContent = ({ close }: { close: () => void }) => (
    <>
      {(user?.first_name || user?.email) && (
        <div className="px-4 pt-3 pb-2">
          {user?.first_name && (
            <p className="text-sm font-semibold text-text-primary truncate">
              {user.first_name} {user.last_name ?? ''}
            </p>
          )}
          {user?.email && <p className="text-xs text-text-quaternary truncate">{user.email}</p>}
        </div>
      )}
      <DropdownDivider />
      {accountItems.map((item) => (
        <AccountMenuItem key={item.href} href={item.href} onClick={close} icon={item.icon}>
          {item.label}
        </AccountMenuItem>
      ))}
      <DropdownDivider />
      <AccountMenuItem href={ROUTES.MANUAL} onClick={close} icon={<BookOpen className="h-4 w-4" />}>
        {tManual('navLabel')}
      </AccountMenuItem>
      <DropdownDivider />
      <button
        type="button"
        role="menuitem"
        onClick={() => {
          close();
          signOut();
        }}
        className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
      >
        <LogOut className="h-4 w-4" />
        {tCommon('signOut')}
      </button>
    </>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-border-primary/60 bg-surface-secondary/80 backdrop-blur-xl shadow-[0_1px_3px_0_rgb(0,0,0,0.03)] dark:bg-surface-secondary/75 dark:border-border-primary dark:shadow-[0_1px_0_0_rgba(255,255,255,0.03)]">
      <div className="mx-auto max-w-[1400px] px-4 md:px-6 py-3 md:py-3.5 flex items-center justify-between gap-4">
        <Link href={ROUTES.HOME} className="group flex items-center gap-2 text-xl font-bold tracking-tight text-text-primary hover:text-teal-700 transition-colors">
          <PawPrint className="h-6 w-6 text-teal-600 group-hover:rotate-[-8deg] transition-transform duration-300" />
          Tu&nbsp;Huella
        </Link>

        <nav className="hidden lg:flex items-center gap-1 xl:gap-1.5 2xl:gap-2 text-sm font-medium text-text-secondary">
          {publicNav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`relative px-3 py-2 rounded-lg transition-colors duration-200 hover:bg-surface-hover hover:text-text-primary ${
                isActive(item.href) ? 'text-teal-700 dark:text-teal-300 font-semibold' : ''
              }`}
            >
              {item.label}
              {isActive(item.href) && (
                <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-gradient-to-r from-teal-600 to-teal-400 dark:from-teal-400 dark:to-teal-300" />
              )}
            </Link>
          ))}
          <DropdownMenu
            align="left"
            panelClassName="w-52 py-1"
            trigger={({ open, getTriggerProps }) => (
              <button
                {...getTriggerProps()}
                type="button"
                className={`relative flex items-center gap-1 px-3 py-2 rounded-lg transition-colors duration-200 hover:bg-surface-hover hover:text-text-primary ${
                  isAboutActive ? 'text-teal-700 dark:text-teal-300 font-semibold' : ''
                }`}
              >
                {t('about')}
                <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? 'rotate-180' : ''}`} />
                {isAboutActive && (
                  <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-gradient-to-r from-teal-600 to-teal-400 dark:from-teal-400 dark:to-teal-300" />
                )}
              </button>
            )}
          >
            {({ close }) =>
              aboutSubLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  role="menuitem"
                  className={`block px-4 py-2.5 text-sm transition-colors hover:bg-surface-hover ${
                    isActive(link.href) ? 'text-teal-700 font-semibold' : 'text-text-secondary'
                  }`}
                  onClick={close}
                >
                  {link.label}
                </Link>
              ))
            }
          </DropdownMenu>
        </nav>

        <div className="hidden lg:flex items-center gap-2 xl:gap-2.5 2xl:gap-3">
          <LocaleSwitcher />
          <ThemeToggle />
          <div className="w-px h-5 bg-gradient-to-b from-transparent via-border-secondary to-transparent mx-1" />
          {!isAuthReady ? (
            <div className="flex items-center gap-2">
              <div className="h-8 w-20 rounded-full bg-surface-hover animate-pulse" />
              <div className="h-8 w-24 rounded-full bg-surface-hover animate-pulse" />
            </div>
          ) : isAuthenticated ? (
            <>
              {rolePanel && rolePanel.items.length === 1 && (
                <Link
                  href={rolePanel.items[0].href}
                  className={`flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg ${rolePanel.color.text} ${rolePanel.color.hover} transition-colors`}
                >
                  {rolePanel.icon}
                  {rolePanel.label}
                </Link>
              )}
              {rolePanel && rolePanel.items.length > 1 && (
                <DropdownMenu
                  align="right"
                  panelClassName="w-64 py-1"
                  ariaLabel={rolePanel.label}
                  trigger={({ open, getTriggerProps }) => (
                    <button
                      {...getTriggerProps()}
                      type="button"
                      className={`flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg ${rolePanel.color.text} ${rolePanel.color.hover} transition-colors`}
                    >
                      {rolePanel.icon}
                      {rolePanel.label}
                      <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? 'rotate-180' : ''}`} />
                    </button>
                  )}
                >
                  {({ close }) =>
                    rolePanel.items.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        role="menuitem"
                        onClick={close}
                        className={`flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors hover:bg-surface-hover ${
                          isActive(item.href) ? `${rolePanel.color.text} font-semibold` : 'text-text-secondary'
                        }`}
                      >
                        <span className="w-4 h-4 flex-shrink-0 flex items-center justify-center">{item.icon}</span>
                        {item.label}
                      </Link>
                    ))
                  }
                </DropdownMenu>
              )}
              <DropdownMenu
                align="right"
                panelClassName="w-80"
                panelTestId="notification-dropdown"
                ariaLabel={tNotif('bellTitle')}
                onOpen={() => void fetchNotifications('in_app')}
                trigger={({ getTriggerProps }) => (
                  <button
                    {...getTriggerProps()}
                    type="button"
                    aria-label={tNotif('bellLabel')}
                    className="relative flex items-center justify-center text-sm px-2 py-2 rounded-lg text-text-secondary hover:bg-surface-hover transition-colors"
                  >
                    <Bell className="h-4 w-4" />
                    <UnreadBadge count={unreadCount} className="-top-0.5 -right-0.5" />
                  </button>
                )}
              >
                {notificationContent}
              </DropdownMenu>

              <DropdownMenu
                align="right"
                panelClassName="w-64 py-1"
                ariaLabel={t('account')}
                trigger={({ open, getTriggerProps }) => (
                  <button
                    {...getTriggerProps()}
                    type="button"
                    aria-label={t('openAccountMenu')}
                    className="flex items-center gap-2 text-sm pl-1.5 pr-2 py-1.5 rounded-full border border-border-secondary hover:bg-surface-hover transition-colors"
                  >
                    <span className="h-7 w-7 rounded-full bg-gradient-to-br from-teal-100 to-teal-200 ring-2 ring-surface-primary shadow-sm text-teal-700 flex items-center justify-center text-xs font-bold">
                      {user?.first_name?.[0]?.toUpperCase() ?? <User className="h-3.5 w-3.5" />}
                    </span>
                    <ChevronDown className={`h-3.5 w-3.5 text-text-quaternary transition-transform ${open ? 'rotate-180' : ''}`} />
                  </button>
                )}
              >
                {accountContent}
              </DropdownMenu>
            </>
          ) : (
            <>
              <Link
                href={ROUTES.SIGN_IN}
                className="text-sm border border-border-secondary rounded-full px-4 py-2 text-text-secondary hover:bg-surface-hover btn-base"
              >
                {tCommon('signIn')}
              </Link>
              <Link
                href={ROUTES.SIGN_UP}
                className="bg-gradient-to-r from-teal-600 to-teal-700 text-white rounded-full px-5 py-2 hover:from-teal-500 hover:to-teal-600 shadow-sm hover:shadow-md transition-all duration-200 text-sm font-medium"
              >
                {tCommon('signUp')}
              </Link>
            </>
          )}
        </div>

        {/* ── Tablet nav (768–1023px) ── */}
        <div className="hidden md:flex lg:hidden flex-1 items-center justify-between gap-2">
          <nav className="flex items-center gap-0.5 text-sm font-medium text-text-secondary">
            {publicNav.slice(0, 3).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`relative px-3 py-2 rounded-lg transition-colors duration-200 hover:bg-surface-hover hover:text-text-primary ${
                  isActive(item.href) ? 'text-teal-700 dark:text-teal-300 font-semibold' : ''
                }`}
              >
                {item.label}
                {isActive(item.href) && (
                  <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-gradient-to-r from-teal-600 to-teal-400 dark:from-teal-400 dark:to-teal-300" />
                )}
              </Link>
            ))}
            <DropdownMenu
              align="left"
              panelClassName="w-48 py-1"
              trigger={({ open, getTriggerProps }) => (
                <button
                  {...getTriggerProps()}
                  type="button"
                  className={`flex items-center gap-1 px-3 py-2 rounded-lg transition-colors duration-200 hover:bg-surface-hover hover:text-text-primary ${
                    publicNav.slice(3).some((item) => isActive(item.href)) || isAboutActive
                      ? 'text-teal-700 dark:text-teal-300 font-semibold'
                      : ''
                  }`}
                >
                  {t('more')}
                  <ChevronDown className={`h-3 w-3 transition-transform ${open ? 'rotate-180' : ''}`} />
                </button>
              )}
            >
              {({ close }) => (
                <>
                  {publicNav.slice(3).map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      role="menuitem"
                      className={`block px-4 py-2.5 text-sm transition-colors hover:bg-surface-hover ${
                        isActive(item.href) ? 'text-teal-700 font-semibold' : 'text-text-secondary'
                      }`}
                      onClick={close}
                    >
                      {item.label}
                    </Link>
                  ))}
                  <DropdownDivider />
                  {aboutSubLinks.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      role="menuitem"
                      className={`block px-4 py-2.5 text-sm transition-colors hover:bg-surface-hover ${
                        isActive(link.href) ? 'text-teal-700 font-semibold' : 'text-text-secondary'
                      }`}
                      onClick={close}
                    >
                      {link.label}
                    </Link>
                  ))}
                </>
              )}
            </DropdownMenu>
          </nav>
          <div className="flex items-center gap-1.5">
            <LocaleSwitcher />
            <ThemeToggle />
            <div className="w-px h-5 bg-gradient-to-b from-transparent via-border-secondary to-transparent mx-0.5" />
            {!isAuthReady ? (
              <div className="h-8 w-8 rounded-full bg-surface-hover animate-pulse" />
            ) : isAuthenticated ? (
              <>
                {rolePanel && rolePanel.items.length === 1 && (
                  <Link
                    href={rolePanel.items[0].href}
                    aria-label={rolePanel.label}
                    className={`flex items-center justify-center min-h-[44px] min-w-[44px] rounded-lg ${rolePanel.color.text} ${rolePanel.color.hover} transition-colors`}
                  >
                    {rolePanel.icon}
                  </Link>
                )}
                {rolePanel && rolePanel.items.length > 1 && (
                  <DropdownMenu
                    align="right"
                    panelClassName="w-56 py-1"
                    ariaLabel={rolePanel.label}
                    trigger={({ getTriggerProps }) => (
                      <button
                        {...getTriggerProps()}
                        type="button"
                        aria-label={rolePanel.label}
                        className={`flex items-center justify-center min-h-[44px] min-w-[44px] rounded-lg ${rolePanel.color.text} ${rolePanel.color.hover} transition-colors`}
                      >
                        {rolePanel.icon}
                      </button>
                    )}
                  >
                    {({ close }) =>
                      rolePanel.items.map((item) => (
                        <Link
                          key={item.href}
                          href={item.href}
                          role="menuitem"
                          onClick={close}
                          className={`flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors hover:bg-surface-hover ${
                            isActive(item.href) ? `${rolePanel.color.text} font-semibold` : 'text-text-secondary'
                          }`}
                        >
                          <span className="w-4 h-4 flex-shrink-0 flex items-center justify-center">{item.icon}</span>
                          {item.label}
                        </Link>
                      ))
                    }
                  </DropdownMenu>
                )}
                <DropdownMenu
                  align="right"
                  panelClassName="w-80"
                  panelTestId="notification-dropdown-tablet"
                  ariaLabel={tNotif('bellTitle')}
                  onOpen={() => void fetchNotifications('in_app')}
                  trigger={({ getTriggerProps }) => (
                    <button
                      {...getTriggerProps()}
                      type="button"
                      aria-label={tNotif('bellLabel')}
                      className="relative flex items-center justify-center min-h-[44px] min-w-[44px] rounded-lg text-text-secondary hover:bg-surface-hover transition-colors"
                    >
                      <Bell className="h-4 w-4" />
                      <UnreadBadge count={unreadCount} className="-top-0.5 -right-0.5" />
                    </button>
                  )}
                >
                  {notificationContent}
                </DropdownMenu>
                <DropdownMenu
                  align="right"
                  panelClassName="w-64 py-1"
                  ariaLabel={t('account')}
                  trigger={({ getTriggerProps }) => (
                    <button
                      {...getTriggerProps()}
                      type="button"
                      aria-label={t('openAccountMenu')}
                      className="flex items-center justify-center min-h-[44px] min-w-[44px] rounded-full border border-border-secondary hover:bg-surface-hover transition-colors"
                    >
                      <span className="h-7 w-7 rounded-full bg-gradient-to-br from-teal-100 to-teal-200 ring-2 ring-surface-primary shadow-sm text-teal-700 flex items-center justify-center text-xs font-bold">
                        {user?.first_name?.[0]?.toUpperCase() ?? <User className="h-3.5 w-3.5" />}
                      </span>
                    </button>
                  )}
                >
                  {accountContent}
                </DropdownMenu>
              </>
            ) : (
              <>
                <Link
                  href={ROUTES.SIGN_IN}
                  className="text-sm border border-border-secondary rounded-full px-4 py-2 text-text-secondary hover:bg-surface-hover btn-base"
                >
                  {tCommon('signIn')}
                </Link>
                <Link
                  href={ROUTES.SIGN_UP}
                  className="bg-gradient-to-r from-teal-600 to-teal-700 text-white rounded-full px-4 py-2 hover:from-teal-500 hover:to-teal-600 shadow-sm text-sm font-medium"
                >
                  {tCommon('signUp')}
                </Link>
              </>
            )}
          </div>
        </div>

        <div className="md:hidden flex items-center gap-1">
          {isAuthenticated && (
            <Link
              href={ROUTES.MY_NOTIFICATIONS}
              aria-label={tNotif('bellLabel')}
              className="relative flex items-center justify-center p-3 rounded-lg text-text-secondary hover:bg-surface-hover transition-colors"
            >
              <Bell className="h-5 w-5" />
              <UnreadBadge count={unreadCount} className="top-1 right-1" />
            </Link>
          )}
          <button
            type="button"
            className="p-2.5 rounded-lg hover:bg-surface-hover"
            onClick={() => setMobileState(mobileState === 'open' ? 'closing' : 'open')}
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {mobileState === 'open' ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {mobileState !== 'closed' && (
        // The panel sits inside the sticky header, so it must scroll on its own: an
        // authenticated menu is taller than a phone screen and the page cannot move it.
        // 4.5rem covers the 69px header row above it.
        <div
          className={`md:hidden max-h-[calc(100dvh_-_4.5rem)] overflow-y-auto overscroll-contain border-t border-border-primary bg-surface-secondary/95 backdrop-blur-xl shadow-lg dark:bg-surface-secondary/90 dark:border-border-secondary ${mobileState === 'closing' ? 'animate-scale-out' : 'animate-scale-in'}`}
          onAnimationEnd={() => { if (mobileState === 'closing') setMobileState('closed'); }}
        >
          <nav className="flex flex-col px-6 py-4 gap-1 text-sm font-medium text-text-secondary">
            {publicNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3 py-3 rounded-lg transition-colors ${
                  isActive(item.href) ? 'text-teal-700 dark:text-teal-300 font-semibold' : 'hover:bg-surface-hover'
                }`}
                onClick={() => closeMobile()}
              >
                {item.label}
              </Link>
            ))}
            <p className="px-3 pt-3 pb-1 text-xs font-semibold text-text-quaternary uppercase tracking-wider">{t('about')}</p>
            {aboutSubLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-3 pl-6 rounded-lg transition-colors ${
                  isActive(link.href) ? 'text-teal-700 dark:text-teal-300 font-semibold' : 'hover:bg-surface-hover'
                }`}
                onClick={() => closeMobile()}
              >
                {link.label}
              </Link>
            ))}
            <div className="flex items-center gap-3 px-3 py-2">
              <LocaleSwitcher onSelect={() => closeMobile()} />
              <ThemeToggle />
            </div>
            <hr className="my-2 border-border-primary" />
            {!isAuthReady ? (
              <div className="flex flex-col gap-2 px-3">
                <div className="h-10 rounded-lg bg-surface-hover animate-pulse" />
                <div className="h-10 rounded-lg bg-surface-hover animate-pulse" />
              </div>
            ) : isAuthenticated ? (
              <>
                {rolePanel && (
                  <>
                    <p className={`px-3 pt-3 pb-1 text-xs font-semibold uppercase tracking-wider ${rolePanel.color.text}`}>
                      {rolePanel.label}
                    </p>
                    {rolePanel.items.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={`flex items-center gap-2 px-3 py-3 pl-6 rounded-lg transition-colors ${
                          isActive(item.href) ? `${rolePanel.color.text} font-semibold` : 'hover:bg-surface-hover'
                        }`}
                        onClick={() => closeMobile()}
                      >
                        <span className="w-4 h-4 flex items-center justify-center flex-shrink-0">{item.icon}</span>
                        {item.label}
                      </Link>
                    ))}
                  </>
                )}
                <p className="px-3 pt-3 pb-1 text-xs font-semibold text-text-quaternary uppercase tracking-wider">{t('account')}</p>
                {accountItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="px-3 py-3 pl-6 rounded-lg hover:bg-surface-hover"
                    onClick={() => closeMobile()}
                  >
                    {item.label}
                  </Link>
                ))}
                <Link
                  href={ROUTES.MANUAL}
                  className="px-3 py-3 pl-6 rounded-lg hover:bg-surface-hover"
                  onClick={() => closeMobile()}
                >
                  {tManual('navLabel')}
                </Link>
                <button
                  onClick={() => { signOut(); closeMobile(); }}
                  type="button"
                  className="text-left px-3 py-3 rounded-lg hover:bg-surface-hover text-red-600"
                >
                  {tCommon('signOut')}
                </button>
              </>
            ) : (
              <>
                <Link href={ROUTES.SIGN_IN} className="px-3 py-3 rounded-lg hover:bg-surface-hover" onClick={() => closeMobile()}>
                  {tCommon('signIn')}
                </Link>
                <Link
                  href={ROUTES.SIGN_UP}
                  className="px-3 py-3 rounded-lg bg-gradient-to-r from-teal-600 to-teal-700 text-white text-center hover:from-teal-500 hover:to-teal-600"
                  onClick={() => closeMobile()}
                >
                  {tCommon('signUp')}
                </Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}

function UnreadBadge({ count, className }: { count: number; className: string }) {
  if (count <= 0) return null;
  return (
    <span
      className={`absolute ${className} min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1`}
    >
      {count > 99 ? '99+' : count}
    </span>
  );
}

function AccountMenuItem({
  href,
  onClick,
  icon,
  children,
}: {
  href: string;
  onClick: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      role="menuitem"
      onClick={onClick}
      className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-text-secondary hover:bg-surface-hover transition-colors"
    >
      <span className="w-4 h-4 flex items-center justify-center text-text-quaternary">{icon}</span>
      {children}
    </Link>
  );
}

function buildRolePanel(
  role: UserRole | undefined,
  t: ReturnType<typeof useTranslations<'nav'>>,
): RolePanelConfig | null {
  if (!role) return null;
  switch (role) {
    case 'shelter_admin':
      return {
        label: t('shelterPanel'),
        color: { text: 'text-teal-700', hover: 'hover:bg-teal-50' },
        icon: <LayoutDashboard className="h-4 w-4" />,
        items: [
          { label: t('dashboard'), href: ROUTES.SHELTER_DASHBOARD, icon: <LayoutDashboard className="h-4 w-4" /> },
          { label: t('animalsManage'), href: ROUTES.SHELTER_ANIMALS, icon: <AnimalsIcon className="h-4 w-4" /> },
          { label: t('applications'), href: ROUTES.SHELTER_APPLICATIONS, icon: <ClipboardList className="h-4 w-4" /> },
          { label: t('campaignsManage'), href: ROUTES.SHELTER_CAMPAIGNS, icon: <Megaphone className="h-4 w-4" /> },
          { label: t('donations'), href: ROUTES.SHELTER_DONATIONS, icon: <HandCoins className="h-4 w-4" /> },
          { label: t('updates'), href: ROUTES.SHELTER_UPDATES, icon: <Newspaper className="h-4 w-4" /> },
          { label: t('settings'), href: ROUTES.SHELTER_SETTINGS, icon: <Settings className="h-4 w-4" /> },
        ],
      };
    case 'web_manager':
      return {
        label: t('webManagerPanel'),
        color: { text: 'text-text-secondary', hover: 'hover:bg-surface-hover hover:text-text-primary' },
        icon: <ClipboardList className="h-4 w-4" />,
        items: [
          { label: t('applications'), href: ROUTES.WEB_MANAGER_APPLICATIONS, icon: <ClipboardList className="h-4 w-4" /> },
          { label: t('sheltersManage'), href: ROUTES.WEB_MANAGER_SHELTERS, icon: <Building2 className="h-4 w-4" /> },
          { label: t('campaignsManage'), href: ROUTES.WEB_MANAGER_CAMPAIGNS, icon: <Megaphone className="h-4 w-4" /> },
          // The backend scopes follow-ups with is_web_manager_or_admin -> the
          // UNFILTERED queryset (views/follow_up.py:30-38), so this role is meant
          // to oversee every follow-up. Without this item the page was reachable
          // only by typing the URL.
          { label: t('followUps'), href: ROUTES.VET_FOLLOW_UPS, icon: <Stethoscope className="h-4 w-4" /> },
        ],
      };
    case 'admin':
      return {
        label: t('admin'),
        color: { text: 'text-amber-700', hover: 'hover:bg-amber-50' },
        icon: <Shield className="h-4 w-4" />,
        items: [
          { label: t('dashboard'), href: ROUTES.ADMIN_DASHBOARD, icon: <LayoutDashboard className="h-4 w-4" /> },
          { label: t('approveShelters'), href: ROUTES.ADMIN_APPROVE_SHELTERS, icon: <BadgeCheck className="h-4 w-4" /> },
          { label: t('moderation'), href: ROUTES.ADMIN_MODERATION, icon: <ShieldAlert className="h-4 w-4" /> },
          { label: t('payments'), href: ROUTES.ADMIN_PAYMENTS, icon: <CreditCard className="h-4 w-4" /> },
          { label: t('metrics'), href: ROUTES.ADMIN_METRICS, icon: <BarChart3 className="h-4 w-4" /> },
          { label: t('blogAdmin'), href: ROUTES.ADMIN_BLOG, icon: <BookText className="h-4 w-4" /> },
          // Same grant as web_manager above: is_web_manager_or_admin returns the
          // unfiltered follow-up queryset, so an admin is meant to see them all.
          { label: t('followUps'), href: ROUTES.VET_FOLLOW_UPS, icon: <Stethoscope className="h-4 w-4" /> },
        ],
      };
    case 'veterinarian':
      return {
        label: t('veterinarianPanel'),
        color: { text: 'text-emerald-700', hover: 'hover:bg-emerald-50' },
        icon: <Stethoscope className="h-4 w-4" />,
        items: [
          { label: t('followUps'), href: ROUTES.VET_FOLLOW_UPS, icon: <Stethoscope className="h-4 w-4" /> },
        ],
      };
    default:
      return null;
  }
}
