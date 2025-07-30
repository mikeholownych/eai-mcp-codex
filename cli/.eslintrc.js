module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module',
    project: ['./tsconfig.json'],
  },
  plugins: [
    '@typescript-eslint',
  ],
  ignorePatterns: ['dist/', 'node_modules/', 'lib/', 'config/', 'demo.js', '.eslintrc.js'], // Ignore dist, node_modules, and unconverted JS files
  rules: {
    '@typescript-eslint/no-require-imports': 'off', // Allow require() for now
    '@typescript-eslint/no-unused-vars': ['warn', { 'argsIgnorePattern': '^' }], // Warn on unused vars, ignore args starting with _
    '@typescript-eslint/no-explicit-any': 'off', // Allow any for mock clients
    'no-useless-escape': 'off', // Disable unnecessary escape character warnings
    '@typescript-eslint/no-unused-expressions': 'off', // Disable unused expressions
    'require-yield': 'off', // Disable require-yield for generator functions
    'no-case-declarations': 'off', // Disable no-case-declarations
    'no-constant-condition': 'off', // Disable no-constant-condition for while(true)
  },
  overrides: [
    {
      files: ['*.js'], // Apply these rules only to .js files
      rules: {
        '@typescript-eslint/no-var-requires': 'off', // Allow require in JS files
        '@typescript-eslint/explicit-module-boundary-types': 'off', // No need for explicit types in JS
      },
    },
  ],
};