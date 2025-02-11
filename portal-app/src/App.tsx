import '../global.css';
import dayjs from 'dayjs';
import minMax from 'dayjs/plugin/minMax';
import utc from 'dayjs/plugin/utc';

dayjs.extend(minMax);
dayjs.extend(utc);

import React, {Fragment, memo, useEffect} from 'react';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {ActionSheetProvider} from '@expo/react-native-action-sheet';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import notifee from '@notifee/react-native';
import {I18nProvider} from '@lingui/react';
import {i18n} from '@lingui/core';
import {AppState, LogBox, StatusBar, View} from 'react-native';
import * as SplashScreen from 'expo-splash-screen';
import {useInitI18n} from '@/i18n';
import {loadErrorMessages, loadDevMessages} from '@apollo/client/dev';
import {
  ApolloProvider,
  AppProvider,
  AuthProvider,
} from './components/providers';
import Router from './routes/router';
import {isAndroid} from './common/deviceHelpers';
import {useAppContext} from './hooks/useContexts';
import useAppTrackingRequest from './hooks/useAppTrackingRequest';
import KeyboardService from './services/KeyboardService';
import {ENVIRONMENT} from './config';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

LogBox.ignoreLogs([
  '[Reanimated] Reading from `value` during component render',
]);

// Keep the splash screen visible while we fetch resources
SplashScreen.preventAutoHideAsync();

// Set the animation options. This is optional.
SplashScreen.setOptions({
  duration: 400,
  fade: true,
});

if (__DEV__) {
  // Adds messages only in a dev environment
  loadDevMessages();
  loadErrorMessages();
}

const statusBarProps = isAndroid
  ? {
      backgroundColor: 'transparent' as const,
      barStyle: 'light-content' as const,
      translucent: true,
    }
  : {
      backgroundColor: 'transparent' as const,
      barStyle: 'light-content' as const,
    };

const EnvIndicator = memo(() => {
  const opacity = useSharedValue(1);
  const color = (() => {
    switch (ENVIRONMENT) {
      case 'qa':
        return 'bg-red-200';
      default:
        return 'bg-transparent';
    }
  })();

  useEffect(() => {
    setTimeout(() => {
      opacity.value = withTiming(0, {duration: 500});
    }, 2000);
  }, []);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      opacity: opacity.value,
    };
  });

  return (
    <Animated.View
      style={animatedStyle}
      className={`absolute top-safe mt-2 rounded-full right-safe mr-2 w-3 h-3 pointer-events-none ${color}`}
    />
  );
});

const AppContent = memo(({i18nLoading}: {i18nLoading: boolean}) => {
  const {isInitialized} = useAppContext();
  const isLoading = i18nLoading || !isInitialized;

  useAppTrackingRequest();

  useEffect(() => {
    if (AppState.currentState === 'active') {
      notifee.setBadgeCount(0);
    }

    const subscription = AppState.addEventListener(
      'change',
      async nextAppState => {
        if (nextAppState === 'active') {
          await notifee.setBadgeCount(0);
        }
      },
    );

    return () => {
      subscription.remove();
    };
  }, []);

  useEffect(() => {
    KeyboardService.init();

    return () => {
      KeyboardService.purge();
    };
  }, []);

  useEffect(() => {
    if (!isLoading) {
      SplashScreen.hide();
    }
  }, [isLoading]);

  if (isLoading) {
    return <View />;
  }

  return (
    <Fragment>
      <Router />
      <EnvIndicator />
    </Fragment>
  );
});

const App = memo(() => {
  const loading = useInitI18n();

  return (
    <GestureHandlerRootView>
      <ActionSheetProvider>
        <SafeAreaProvider>
          <I18nProvider i18n={i18n}>
            <StatusBar {...statusBarProps} />
            <AppProvider>
              <ApolloProvider>
                <AuthProvider>
                  <AppContent i18nLoading={loading} />
                </AuthProvider>
              </ApolloProvider>
            </AppProvider>
          </I18nProvider>
        </SafeAreaProvider>
      </ActionSheetProvider>
    </GestureHandlerRootView>
  );
});

export default App;
