'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { ROUTES } from '@/lib/constants';
import type { AdoptionApplication, AdoptionApplicationStatus } from '@/lib/types';

const statusBadge: Record<AdoptionApplicationStatus, string> = {
  submitted: 'bg-amber-50 text-amber-700 ring-amber-200',
  reviewing: 'bg-sky-50 text-sky-700 ring-sky-200',
  interview: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
  approved: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  rejected: 'bg-red-50 text-red-700 ring-red-200',
};

interface AdminApplicationsTableProps {
  items: AdoptionApplication[];
  loading?: boolean;
  showShelter?: boolean;
}

export default function AdminApplicationsTable({
  items,
  loading = false,
  showShelter = true,
}: AdminApplicationsTableProps) {
  const t = useTranslations('webManager');

  if (loading) {
    return (
      <div role="status" aria-label="loading" className="py-10 text-center text-text-tertiary">
        {t('loading')}
      </div>
    );
  }

  if (items.length === 0) {
    return <p className="py-8 text-center text-text-tertiary">{t('noApplications')}</p>;
  }

  return (
    <div className="min-w-0 lg:rounded-2xl lg:border lg:border-border-primary lg:bg-surface-primary">
      {/* Keep one copy of each record when rows become cards below lg. Explicit
          roles preserve table semantics when CSS changes the native displays. */}
      <table role="table" aria-label={t('applicationsTitle')} className="block w-full text-sm lg:table lg:table-fixed">
        <thead role="rowgroup" className="sr-only bg-surface-secondary lg:not-sr-only lg:table-header-group">
          <tr role="row" className="text-left text-xs uppercase tracking-wide text-text-quaternary">
            <th scope="col" className="px-4 py-3">{t('tableAnimal')}</th>
            {showShelter && <th scope="col" className="px-4 py-3">{t('tableShelter')}</th>}
            <th scope="col" className="px-4 py-3">{t('tableApplicant')}</th>
            <th scope="col" className="px-4 py-3">{t('tableStatus')}</th>
            <th scope="col" className="px-4 py-3">{t('tableCreatedAt')}</th>
          </tr>
        </thead>
        <tbody role="rowgroup" className="grid gap-4 lg:table-row-group">
          {items.map((app) => (
            <tr
              key={app.id}
              role="row"
              className="grid min-w-0 rounded-2xl border border-border-primary bg-surface-primary transition-colors hover:bg-surface-hover lg:table-row lg:rounded-none lg:border-0 lg:border-t lg:border-border-tertiary"
            >
              <td role="cell" className="block min-w-0 px-4 py-3 font-medium text-text-primary lg:table-cell">
                <span aria-hidden="true" className="mb-1 block text-xs text-text-quaternary lg:hidden">{t('tableAnimal')}</span>
                <Link
                  href={ROUTES.WEB_MANAGER_APPLICATION_DETAIL(app.id)}
                  className="inline-flex min-h-11 min-w-11 max-w-full items-center wrap-anywhere transition-colors hover:text-teal-600"
                >
                  {app.animal_name}
                </Link>
              </td>
              {showShelter && (
                <td role="cell" className="block min-w-0 px-4 py-3 wrap-anywhere text-text-secondary lg:table-cell">
                  <span aria-hidden="true" className="mb-1 block text-xs text-text-quaternary lg:hidden">{t('tableShelter')}</span>
                  {app.shelter_name ?? '—'}
                </td>
              )}
              <td role="cell" className="block min-w-0 px-4 py-3 wrap-anywhere text-text-secondary lg:table-cell">
                <span aria-hidden="true" className="mb-1 block text-xs text-text-quaternary lg:hidden">{t('tableApplicant')}</span>
                {app.user_email}
              </td>
              <td role="cell" className="block min-w-0 px-4 py-3 lg:table-cell">
                <span aria-hidden="true" className="mb-1 block text-xs text-text-quaternary lg:hidden">{t('tableStatus')}</span>
                <span className={`inline-flex text-xs px-2 py-1 rounded-full ring-1 font-medium ${statusBadge[app.status]}`}>
                  {t(`status.${app.status}`)}
                </span>
              </td>
              <td role="cell" className="block min-w-0 px-4 py-3 text-text-tertiary lg:table-cell">
                <span aria-hidden="true" className="mb-1 block text-xs text-text-quaternary lg:hidden">{t('tableCreatedAt')}</span>
                {new Date(app.created_at).toLocaleDateString('es')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
