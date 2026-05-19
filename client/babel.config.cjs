module.exports = {
    presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }],
    ],
    plugins: [
        '@babel/plugin-syntax-import-meta',
        function inlineImportMeta() {
            return {
                visitor: {
                    MetaProperty(path) {
                        path.replaceWithSourceString('({ env: { BASE_URL: "/" } })');
                    },
                },
            };
        },
    ],
};
