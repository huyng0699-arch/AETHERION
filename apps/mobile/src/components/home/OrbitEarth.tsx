import React, { useEffect, useRef } from 'react';
import { Animated, Platform, StyleSheet, View } from 'react-native';
import { useTheme } from '../../theme';

const EARTH = require('../../../assets/truy-tinh-cosmic-orbit.png');

/** Decorative orbital illustration, independent of any live mission data. */
export function OrbitEarth({ size = 160 }: { size?: number }) {
  const { appearance } = useTheme();
  const drift = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (appearance.reduceMotion) {
      drift.setValue(0);
      return;
    }
    const animation = Animated.loop(Animated.sequence([
      Animated.timing(drift, { toValue: 1, duration: 5000, useNativeDriver: Platform.OS !== 'web' }),
      Animated.timing(drift, { toValue: 0, duration: 5000, useNativeDriver: Platform.OS !== 'web' }),
    ]));
    animation.start();
    return () => animation.stop();
  }, [appearance.reduceMotion, drift]);

  return <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={{ width: size, height: size }}>
    <View style={[styles.orbit, { width: size * 1.12, height: size * 0.46, left: -size * 0.06, top: size * 0.27, borderRadius: size }]} />
    <Animated.Image source={EARTH} resizeMode="contain" style={{ width: size, height: size, transform: [{ translateY: drift.interpolate({ inputRange: [0, 1], outputRange: [0, -4] }) }] }} />
    <View style={[styles.satellite, { left: size * 0.84, top: size * 0.27 }]} />
  </View>;
}

const styles = StyleSheet.create({
  orbit: { position: 'absolute', borderWidth: 1, borderColor: 'rgba(190,209,255,0.38)', transform: [{ rotate: '-24deg' }] },
  satellite: { position: 'absolute', width: 5, height: 5, borderRadius: 3, backgroundColor: '#AFE8FF' },
});
