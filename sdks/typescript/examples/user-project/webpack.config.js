const path = require('path');
const { LilypadWebpackPlugin } = require('@lilypad/typescript-sdk/webpack');

module.exports = {
  mode: 'production',
  entry: './src/index.ts',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'index.js',
    library: {
      type: 'module',
    },
  },
  experiments: {
    outputModule: true,
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  plugins: [
    new LilypadWebpackPlugin({
      tsConfig: './tsconfig.json',
      output: 'lilypad-metadata.json',
      include: ['src/**/*.ts'],
      verbose: true,
    }),
  ],
  externals: {
    '@lilypad/typescript-sdk': '@lilypad/typescript-sdk',
  },
};
