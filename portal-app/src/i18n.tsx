import {i18n} from '@lingui/core';
import * as Localization from 'expo-localization';
import {useEffect, useState} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {messages as enMessages} from './locales/en.po';

const LANGUAGE_KEY = 'app_language';

export type SupportedLocales = 'en';
export const defaultLocale: SupportedLocales = 'en';

export const locales: SupportedLocales[] = ['en'];

const messages = {
  en: enMessages,
};

export async function activateLocale(locale: SupportedLocales) {
  try {
    i18n.load(locale, messages[locale]);
    i18n.activate(locale);
    await AsyncStorage.setItem(LANGUAGE_KEY, locale);
  } catch (error) {
    console.error('Error loading messages:', error);
    // Fallback to default locale if loading fails
    if (locale !== defaultLocale) {
      await activateLocale(defaultLocale);
    }
  }
}

export function useInitI18n() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function init() {
      try {
        // Try to get stored language preference
        const storedLanguage = await AsyncStorage.getItem(LANGUAGE_KEY);

        // If no stored preference, use device locale
        let targetLocale = storedLanguage as SupportedLocales;
        if (!targetLocale) {
          const deviceLocales = Localization.getLocales();
          // Get the languageCode from the first locale in the array
          const deviceLanguage = deviceLocales[0]?.languageCode;

          targetLocale =
            deviceLanguage &&
            locales.includes(deviceLanguage as SupportedLocales)
              ? (deviceLanguage as SupportedLocales)
              : defaultLocale;
        }

        await activateLocale(targetLocale);
      } catch (error) {
        console.error('Error initializing i18n:', error);
        // Fallback to default locale
        await activateLocale(defaultLocale);
      } finally {
        setLoading(false);
      }
    }

    init();
  }, []);

  return loading;
}
