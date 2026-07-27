// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'CORTEX.DEV',
			customCss: ['./src/styles/custom.css'],
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/borjamoskv/Cortex-Persist' }],
			sidebar: [
				{
					label: 'SDK Reference',
					items: [
						{ label: 'Write-Path Contract (SAGA)', slug: 'guides/saga' },
					],
				},
				{
					label: 'API Reference',
					items: [{ autogenerate: { directory: 'reference' } }],
				},
			],
		}),
	],
});
