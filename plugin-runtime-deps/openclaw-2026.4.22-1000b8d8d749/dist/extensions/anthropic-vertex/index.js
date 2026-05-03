import { n as NATIVE_ANTHROPIC_REPLAY_HOOKS } from "../../provider-model-shared-DWfF4VYg.js";
import { t as definePluginEntry } from "../../plugin-entry-DhR2SXKx.js";
import { i as resolveAnthropicVertexConfigApiKey } from "../../region-DwurVGyJ.js";
import { n as resolveImplicitAnthropicVertexProvider, t as mergeImplicitAnthropicVertexProvider } from "../../api--ix7xLfw.js";
//#region extensions/anthropic-vertex/index.ts
const PROVIDER_ID = "anthropic-vertex";
var anthropic_vertex_default = definePluginEntry({
	id: PROVIDER_ID,
	name: "Anthropic Vertex Provider",
	description: "Bundled Anthropic Vertex provider plugin",
	register(api) {
		api.registerProvider({
			id: PROVIDER_ID,
			label: "Anthropic Vertex",
			docsPath: "/providers/models",
			auth: [],
			catalog: {
				order: "simple",
				run: async (ctx) => {
					const implicit = resolveImplicitAnthropicVertexProvider({ env: ctx.env });
					if (!implicit) return null;
					return { provider: mergeImplicitAnthropicVertexProvider({
						existing: ctx.config.models?.providers?.[PROVIDER_ID],
						implicit
					}) };
				}
			},
			resolveConfigApiKey: ({ env }) => resolveAnthropicVertexConfigApiKey(env),
			...NATIVE_ANTHROPIC_REPLAY_HOOKS
		});
	}
});
//#endregion
export { anthropic_vertex_default as default };
