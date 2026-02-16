// @ts-check
import withNuxt from "./.nuxt/eslint.config.mjs";

export default withNuxt({
  rules: {
    // Allow console.warn and console.error for debugging/logging
    "no-console": ["warn", { allow: ["warn", "error"] }],
    // Relax unused vars rule to allow underscore-prefixed variables
    "@typescript-eslint/no-unused-vars": [
      "warn",
      { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
    ],
    // Vue specific relaxations
    "vue/multi-word-component-names": "off",
    // Downgrade to warn for gradual adoption — fix these over time
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/ban-ts-comment": "warn",
    "@typescript-eslint/unified-signatures": "warn",
    "@typescript-eslint/no-dynamic-delete": "warn",
    "vue/no-mutating-props": "warn",
    "prefer-rest-params": "warn",
  },
});
