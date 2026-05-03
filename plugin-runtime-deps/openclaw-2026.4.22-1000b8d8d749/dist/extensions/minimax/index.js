import { t as definePluginEntry } from "../../plugin-entry-DhR2SXKx.js";
import { n as buildMinimaxPortalImageGenerationProvider, t as buildMinimaxImageGenerationProvider } from "../../image-generation-provider-hvLe0RPg.js";
import { n as minimaxPortalMediaUnderstandingProvider, t as minimaxMediaUnderstandingProvider } from "../../media-understanding-provider-bHFep-rW.js";
import { t as buildMinimaxMusicGenerationProvider } from "../../music-generation-provider-DgNq1gTh.js";
import { t as registerMinimaxProviders } from "../../provider-registration-TtG2S-8P.js";
import { t as buildMinimaxSpeechProvider } from "../../speech-provider-Bhu8bOMf.js";
import { t as createMiniMaxWebSearchProvider } from "../../minimax-web-search-provider-BWhaOy0o.js";
import { t as buildMinimaxVideoGenerationProvider } from "../../video-generation-provider-ClCEKr6g.js";
//#region extensions/minimax/index.ts
var minimax_default = definePluginEntry({
	id: "minimax",
	name: "MiniMax",
	description: "Bundled MiniMax API-key and OAuth provider plugin",
	register(api) {
		registerMinimaxProviders(api);
		api.registerMediaUnderstandingProvider(minimaxMediaUnderstandingProvider);
		api.registerMediaUnderstandingProvider(minimaxPortalMediaUnderstandingProvider);
		api.registerImageGenerationProvider(buildMinimaxImageGenerationProvider());
		api.registerImageGenerationProvider(buildMinimaxPortalImageGenerationProvider());
		api.registerMusicGenerationProvider(buildMinimaxMusicGenerationProvider());
		api.registerVideoGenerationProvider(buildMinimaxVideoGenerationProvider());
		api.registerSpeechProvider(buildMinimaxSpeechProvider());
		api.registerWebSearchProvider(createMiniMaxWebSearchProvider());
	}
});
//#endregion
export { minimax_default as default };
