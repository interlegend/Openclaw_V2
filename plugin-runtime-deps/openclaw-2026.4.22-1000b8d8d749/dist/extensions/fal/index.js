import { t as definePluginEntry } from "../../plugin-entry-DhR2SXKx.js";
import { n as buildFalImageGenerationProvider } from "../../image-generation-provider-4T53ms0v.js";
import { t as createFalProvider } from "../../provider-registration-BFCYQa8O.js";
import { n as buildFalVideoGenerationProvider } from "../../video-generation-provider-DN97KAxq.js";
var fal_default = definePluginEntry({
	id: "fal",
	name: "fal Provider",
	description: "Bundled fal image and video generation provider",
	register(api) {
		api.registerProvider(createFalProvider());
		api.registerImageGenerationProvider(buildFalImageGenerationProvider());
		api.registerVideoGenerationProvider(buildFalVideoGenerationProvider());
	}
});
//#endregion
export { fal_default as default };
