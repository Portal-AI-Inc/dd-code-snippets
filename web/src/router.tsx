'use client';

import {FC, Suspense, lazy} from 'react';
import {
  createBrowserRouter,
  Navigate,
  Outlet,
  RouteObject,
} from 'react-router-dom';
import {wrapCreateBrowserRouter} from '@sentry/react';
import PortalSpinner from './components/PortalSpinner';
import ErrorPage from './ErrorPage';
import StripeSuccess from './routes/StripeSuccess';
import StripeMobileRedirect from './routes/StripeMobileRedirect';
import LegalDocument from './routes/legal/LegalDocument';
import ProtectedRoute from './routes/components/ProtectedRoute';

import AuthRedirect from './routes/AuthRedirect';
import {
  SearchParamsProvider,
  ErrorParamHandlerProvider,
} from './components/providers';
import Root from './routes/Root';
import MetaAdsAuth from './routes/MetaAdsAuth';

import PageContainer from './components/PageContainer';


import Onboarding from './routes/Onboarding';
import OnboardingConnectShopify from './routes/Onboarding/OnboardingConnectShopify';

/* eslint-disable react-refresh/only-export-components */

const Loader: FC = () => (
  <PortalSpinner
    classNames={{
      base: 'backdrop-blur-sm fixed inset-0 z-[1000]',
    }}
    size="lg"
  />
);

const withSuspense = (Component: FC) => {
  const SuspenseWrapper: FC = () => (
    <Suspense fallback={<Loader />}>
      <Component />
    </Suspense>
  );

  return SuspenseWrapper;
};

const Legal = withSuspense(lazy(() => import('./routes/legal')));
const TermsRoute = withSuspense(() => (
  <LegalDocument file={import('@/assets/legal/terms.md?raw')} />
));
const PrivacyRoute = withSuspense(() => (
  <LegalDocument file={import('@/assets/legal/privacy.md?raw')} />
));
const DataProcessingAddendumRoute = withSuspense(() => (
  <LegalDocument
    file={import('@/assets/legal/data-processing-addendum.md?raw')}
  />
));
const SubprocessorsRoute = withSuspense(() => (
  <LegalDocument file={import('@/assets/legal/subprocessors.md?raw')} />
));
const NotFound = withSuspense(lazy(() => import('./routes/NotFound')));

const authPath: RouteObject = {
  path: 'auth',
  element: <Outlet />,
  children: [
    {
      path: 'redirect',
      element: <AuthRedirect />,
    },
  ],
};


const router = wrapCreateBrowserRouter(createBrowserRouter)([
  {
    path: '/',
    element: (
      <SearchParamsProvider>
        <ErrorParamHandlerProvider>
          <Root />
        </ErrorParamHandlerProvider>
      </SearchParamsProvider>
    ),
    errorElement: <ErrorPage />,
    children: [
      authPath,
      {
        path: 'stripe-success',
        element: (
          <ProtectedRoute redirectTo="/onboarding">
            <StripeSuccess />
          </ProtectedRoute>
        ),
      },
      {
        path: 'stripe-mobile-redirect',
        element: <StripeMobileRedirect />,
      },
      {
        path: 'meta-ads-auth',
        element: <MetaAdsAuth />,
      },
      {
        path: 'legal',
        element: (
          <PageContainer>
            <Outlet />
          </PageContainer>
        ),
        children: [
          {
            path: '',
            element: <Legal />,
          },
          {
            path: 'terms',
            element: <TermsRoute />,
          },
          {
            path: 'privacy',
            element: <PrivacyRoute />,
          },
          {
            path: 'data-processing-addendum',
            element: <DataProcessingAddendumRoute />,
          },
          {
            path: 'subprocessors',
            element: <SubprocessorsRoute />,
          },
        ],
      },

      {
        path: 'onboarding',
        element: (
          <PageContainer color="default">
            <Onboarding />
          </PageContainer>
        ),
        children: [
          {
            path: 'connect-shopify',
            element: <OnboardingConnectShopify />,
          },
        ],
      },
      {path: '', element: <Navigate to="/onboarding" replace />},
      {path: '*', element: <NotFound />},
    ],
  },
]);

export default router;
