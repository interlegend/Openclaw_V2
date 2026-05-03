import { a as buildProviderToolCompatFamilyHooks } from "../../provider-tools-f43A-LwX.js";
import { t as definePluginEntry } from "../../plugin-entry-DhR2SXKx.js";
import { r as resolvePluginConfigObject } from "../../config-runtime-DEszYLsI.js";
import { t as buildOpenAICodexCliBackend } from "../../cli-backend-_Vucys6j.js";
import { t as buildOpenAIImageGenerationProvider } from "../../image-generation-provider-Dk8cl4uQ.js";
import { n as openaiCodexMediaUnderstandingProvider, r as openaiMediaUnderstandingProvider } from "../../media-understanding-provider-gXi2iA-6.js";
import { t as openAiMemoryEmbeddingProviderAdapter } from "../../memory-embedding-adapter-B8-9pNTl.js";
import { t as buildOpenAICodexProviderPlugin } from "../../openai-codex-provider-CqWyH5Qs.js";
import { t as buildOpenAIProvider } from "../../openai-provider-BilNzjLL.js";
import { i as resolveOpenAISystemPromptContribution, r as resolveOpenAIPromptOverlayMode } from "../../prompt-overlay-BKYpmcXA.js";
import { t as buildOpenAIRealtimeTranscriptionProvider } from "../../realtime-transcription-provider-yoFnVEkR.js";
import { t as buildOpenAIRealtimeVoiceProvider } from "../../realtime-voice-provider-DgaIAMDb.js";
import { t as buildOpenAISpeechProvider } from "../../speech-provider-Dwn25Vsl.js";
import { t as buildOpenAIVideoGenerationProvider } from "../../video-generation-provider-CglMjjJn.js";
//#region extensions/openai/index.ts
var openai_default = definePluginEntry({
	id: "openai",
	name: "OpenAI Provider",
	description: "Bundled OpenAI provider plugins",
	register(api) {
		const openAIToolCompatHooks = buildProviderToolCompatFamilyHooks("openai");
		const buildProviderWithPromptContribution = (provider) => ({
			...provider,
			...openAIToolCompatHooks,
			resolveSystemPromptContribution: (ctx) => {
				const pluginConfig = resolvePluginConfigObject(ctx.config, "openai") ?? (ctx.config ? void 0 : api.pluginConfig);
				return resolveOpenAISystemPromptContribution({
					config: ctx.config,
					legacyPluginConfig: pluginConfig,
					mode: resolveOpenAIPromptOverlayMode(pluginConfig),
					modelProviderId: provider.id,
					modelId: ctx.modelId
				});
			}
		});
		api.registerCliBackend(buildOpenAICodexCliBackend());
		api.registerProvider(buildProviderWithPromptContribution(buildOpenAIProvider()));
		api.registerProvider(buildProviderWithPromptContribution(buildOpenAICodexProviderPlugin()));
		api.registerMemoryEmbeddingProvider(openAiMemoryEmbeddingProviderAdapter);
		api.registerImageGenerationProvider(buildOpenAIImageGenerationProvider());
		api.registerRealtimeTranscriptionProvider(buildOpenAIRealtimeTranscriptionProvider());
		api.registerRealtimeVoiceProvider(buildOpenAIRealtimeVoiceProvider());
		api.registerSpeechProvider(buildOpenAISpeechProvider());
		api.registerMediaUnderstandingProvider(openaiMediaUnderstandingProvider);
		api.registerMediaUnderstandingProvider(openaiCodexMediaUnderstandingProvider);
		api.registerVideoGenerationProvider(buildOpenAIVideoGenerationProvider());
	}
});
//#endregion
export { openai_default as default };
