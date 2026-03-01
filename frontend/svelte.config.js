import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			pages: '../src/skaro_web/static',
			assets: '../src/skaro_web/static',
			fallback: 'index.html'
		}),
		paths: {
			base: ''
		}
	}
};

export default config;
