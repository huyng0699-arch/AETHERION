const base = require('./app.json');

module.exports = ({ config }) => {
  const allowDevelopmentHttp = process.env.AETHERION_ALLOW_DEV_HTTP === '1';
  return {
    ...base.expo,
    ...config,
    android: {
      ...base.expo.android,
      ...config.android,
      // Development-only opt-in. Release builds remain HTTPS-only by default.
      usesCleartextTraffic: allowDevelopmentHttp,
    },
  };
};
