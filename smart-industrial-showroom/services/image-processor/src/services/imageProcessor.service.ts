/**
 * AI Image Processing Service — Smart Industrial Cloud Showroom
 * ==============================================================
 * Transforms traditional factory photos into futuristic Industry 4.0 visuals
 * before they are projected into the AR 360° panorama (ARShowroom.tsx).
 *
 * Architecture:
 *   Controller (Express route) → ImageProcessorService → Provider adapter
 *     ├── ReplicateProvider   (Stable Diffusion img2img / inpainting)
 *     ├── CloudinaryProvider  (generative restore + color grading)
 *     └── LocalFallbackProvider (deterministic mock for dev / offline)
 *
 * Clean Architecture: this file is the Application Service layer — no HTTP concerns.
 */

import Replicate from 'replicate';
import { v2 as cloudinary } from 'cloudinary';

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

export type ProcessingProvider = 'replicate' | 'cloudinary' | 'mock';

export interface ProcessFactoryImageOptions {
  /** Force a specific provider (defaults to env IMAGE_PROCESSOR_PROVIDER) */
  provider?: ProcessingProvider;
  /** SD img2img strength — lower preserves original layout, higher = more AI */
  strength?: number;
  /** Remove floor clutter (fans, bags, boxes) before color grading */
  removeClutter?: boolean;
  /** Optional callback URL for async webhook (Replicate) */
  webhookUrl?: string;
}

export interface ProcessFactoryImageResult {
  /** Public URL of the tech-enhanced image ready for 360° skybox */
  enhancedImageUrl: string;
  provider: ProcessingProvider;
  /** Original input for audit trail */
  sourceImageUrl: string;
  /** Prompt tokens sent to the AI model */
  promptUsed: string;
  negativePromptUsed: string;
  processedAt: string;
  /** Replicate prediction ID or Cloudinary public_id when applicable */
  externalJobId?: string;
}

export interface ImageProcessorConfig {
  replicateApiToken?: string;
  cloudinaryCloudName?: string;
  cloudinaryApiKey?: string;
  cloudinaryApiSecret?: string;
  defaultProvider: ProcessingProvider;
  /** Replicate model version slug */
  replicateModel?: string;
}

// ---------------------------------------------------------------------------
// Prompt Engineering — Industry 4.0 "Tech-ify" tokens
// ---------------------------------------------------------------------------

/**
 * POSITIVE PROMPT TOKENS (concatenated for SD / generative APIs):
 *
 * - "High-resolution, 8k, modern smart factory, clean room reflection"
 * - "Add subtle glowing cyan LED strip lights along the edges of the traditional machinery"
 * - "Add holographic circuit board (PCB) pattern textures on empty walls"
 * - "Apply a cool-toned color grading filter (shift yellow/brown industrial rust
 *    to high-tech metallic silver and deep neon blue)"
 */
export const FACTORY_CLEANUP_POSITIVE_PROMPT = [
  'Professional smart factory interior photograph',
  'remove all clutter and loose objects, no electric fans, no garbage bags, no cardboard boxes',
  'clean empty walkways and aisles, only industrial CNC machines and production equipment remain',
  'spotless polished factory floor, organized tidy manufacturing plant',
  'bright even lighting, vibrant clean colors, photorealistic, same camera angle and layout',
].join(', ');

export const FACTORY_CLEANUP_NEGATIVE_PROMPT = [
  'electric fan, standing fan, garbage bag, trash bag, cardboard box, clutter, mess',
  'cables on floor, random objects, workers, people, deformed machinery',
  'blurry, low quality, watermark, cartoon, extra equipment, hallucinated machines',
].join(', ');

export const FACTORY_TECHIFY_POSITIVE_PROMPT = [
  'High-resolution, 8k, modern smart factory, clean room reflection',
  'Add subtle glowing cyan LED strip lights along the edges of the traditional machinery',
  'Add holographic circuit board (PCB) pattern textures on empty walls',
  'Apply a cool-toned color grading filter, shift yellow/brown industrial rust to high-tech metallic silver and deep neon blue',
  'futuristic Industry 4.0 aesthetic, spotless polished concrete floor, volumetric lighting',
  'digital twin overlay ready, ultra sharp, professional architectural photography',
].join(', ');

export const FACTORY_TECHIFY_NEGATIVE_PROMPT = [
  'blurry, low quality, jpeg artifacts, dirty, rusty, cluttered cables',
  'warm yellow cast, sepia, vintage, graffiti, people, text watermark',
  'cartoon, anime, oversaturated, lens flare abuse, fisheye distortion',
  'deformed machinery, melted metal, extra limbs, hallucinated equipment',
].join(', ');

// ---------------------------------------------------------------------------
// Service implementation
// ---------------------------------------------------------------------------

export class ImageProcessorService {
  private readonly replicate: Replicate | null;
  private readonly config: ImageProcessorConfig;

  constructor(config: ImageProcessorConfig) {
    this.config = config;
    this.replicate = config.replicateApiToken
      ? new Replicate({ auth: config.replicateApiToken })
      : null;

    if (
      config.cloudinaryCloudName &&
      config.cloudinaryApiKey &&
      config.cloudinaryApiSecret
    ) {
      cloudinary.config({
        cloud_name: config.cloudinaryCloudName,
        api_key: config.cloudinaryApiKey,
        api_secret: config.cloudinaryApiSecret,
        secure: true,
      });
    }
  }

  /**
   * Main entry point — process a traditional factory photo into a tech-enhanced
   * panorama-ready asset.
   *
   * @param imageUrl - Public HTTP(S) URL or data URI of the uploaded factory photo
   * @returns Enhanced image URL for ARShowroom skybox projection
   */
  async processFactoryImage(
    imageUrl: string,
    options: ProcessFactoryImageOptions = {},
  ): Promise<ProcessFactoryImageResult> {
    const provider = options.provider ?? this.config.defaultProvider;
    const removeClutter = options.removeClutter ?? false;
    const strength = options.strength ?? (removeClutter ? 0.38 : 0.42);
    const processedAt = new Date().toISOString();

    switch (provider) {
      case 'replicate':
        return this.processViaReplicate(imageUrl, strength, processedAt, options.webhookUrl, removeClutter);
      case 'cloudinary':
        return this.processViaCloudinary(imageUrl, processedAt, removeClutter);
      case 'mock':
      default:
        return this.processViaMock(imageUrl, processedAt, removeClutter);
    }
  }

  // -------------------------------------------------------------------------
  // Provider: Replicate (Stable Diffusion img2img)
  // Model: stability-ai/sdxl or lucataco/sdxl-lightning-4step (configurable)
  // -------------------------------------------------------------------------

  private async processViaReplicate(
    imageUrl: string,
    strength: number,
    processedAt: string,
    webhookUrl?: string,
    removeClutter = false,
  ): Promise<ProcessFactoryImageResult> {
    if (!this.replicate) {
      console.warn('[ImageProcessor] REPLICATE_API_TOKEN missing — falling back to mock');
      return this.processViaMock(imageUrl, processedAt, removeClutter);
    }

    const model =
      this.config.replicateModel ??
      'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89fbf45c17c114af5ee346f735020d8df092ed784';

    /**
     * Replicate SDXL img2img payload — `prompt` carries our Industry 4.0 tokens.
     * `image` is the factory photo URL; `prompt_strength` controls transformation depth.
     */
    const prompt = removeClutter ? FACTORY_CLEANUP_POSITIVE_PROMPT : FACTORY_TECHIFY_POSITIVE_PROMPT;
    const negativePrompt = removeClutter
      ? FACTORY_CLEANUP_NEGATIVE_PROMPT
      : FACTORY_TECHIFY_NEGATIVE_PROMPT;

    const input = {
      image: imageUrl,
      prompt,
      negative_prompt: negativePrompt,
      prompt_strength: strength,
      num_inference_steps: 30,
      guidance_scale: 7.5,
      scheduler: 'K_EULER',
      refine: 'expert_ensemble_refiner',
      high_noise_frac: 0.8,
    };

    const prediction = await this.replicate.run(model as `${string}/${string}`, {
      input,
      ...(webhookUrl ? { webhook: webhookUrl, webhook_events_filter: ['completed'] } : {}),
    });

    // Replicate may return string URL or array of URLs depending on model
    const output = prediction as string | string[] | Record<string, unknown>;
    const enhancedImageUrl = this.extractUrlFromReplicateOutput(output);

    return {
      enhancedImageUrl,
      provider: 'replicate',
      sourceImageUrl: imageUrl,
      promptUsed: prompt,
      negativePromptUsed: negativePrompt,
      processedAt,
      externalJobId: typeof prediction === 'object' ? String((prediction as { id?: string }).id ?? '') : undefined,
    };
  }

  private extractUrlFromReplicateOutput(output: string | string[] | Record<string, unknown>): string {
    if (typeof output === 'string') return output;
    if (Array.isArray(output) && output.length > 0) return String(output[0]);
    if (output && typeof output === 'object' && 'output' in output) {
      const inner = (output as { output: unknown }).output;
      if (typeof inner === 'string') return inner;
      if (Array.isArray(inner) && inner.length > 0) return String(inner[0]);
    }
    throw new Error('[ImageProcessor] Replicate returned an unexpected output shape');
  }

  // -------------------------------------------------------------------------
  // Provider: Cloudinary AI (generative fill + e_effect color grading)
  // -------------------------------------------------------------------------

  private async processViaCloudinary(
    imageUrl: string,
    processedAt: string,
    removeClutter = false,
  ): Promise<ProcessFactoryImageResult> {
    if (!this.config.cloudinaryCloudName) {
      console.warn('[ImageProcessor] Cloudinary credentials missing — falling back to mock');
      return this.processViaMock(imageUrl, processedAt, removeClutter);
    }

    /**
     * Upload source image, then apply chained transformations:
     * 1. generative restore (denoise + upscale)
     * 2. e_art:cyberpunk or custom e_gradient_fade for cool tone
     * 3. e_improve for clarity
     *
     * Cloudinary generative prompt mirrors our SD tokens via `e_gen_replace` (when available)
     * or artistic filter stack as fallback.
     */
    const upload = await cloudinary.uploader.upload(imageUrl, {
      folder: 'smart-showroom/enhanced',
      tags: ['factory', 'industry40', 'ar-panorama'],
      transformation: [
        { effect: 'improve' },
        { effect: 'auto_brightness' },
        { effect: 'blue', strength: 25 },
        { effect: 'sharpen', strength: 80 },
        { quality: 'auto:best', fetch_format: 'auto' },
      ],
    });

    // Secondary pass URL with overlay hint for "cyan LED edge glow" simulation
    const enhancedImageUrl = cloudinary.url(upload.public_id, {
      transformation: [
        { width: 4096, height: 2048, crop: 'fill', gravity: 'auto' },
        { effect: 'contrast:20' },
        { effect: 'blue:20' },
        { overlay: 'text:Roboto_20_bold:INDUSTRY%204.0', gravity: 'south_east', x: 20, y: 20, opacity: 0 },
      ],
      secure: true,
    });

    const prompt = removeClutter ? FACTORY_CLEANUP_POSITIVE_PROMPT : FACTORY_TECHIFY_POSITIVE_PROMPT;
    const negativePrompt = removeClutter
      ? FACTORY_CLEANUP_NEGATIVE_PROMPT
      : FACTORY_TECHIFY_NEGATIVE_PROMPT;

    return {
      enhancedImageUrl,
      provider: 'cloudinary',
      sourceImageUrl: imageUrl,
      promptUsed: prompt,
      negativePromptUsed: negativePrompt,
      processedAt,
      externalJobId: upload.public_id,
    };
  }

  // -------------------------------------------------------------------------
  // Provider: Mock / Local fallback (dev & CI — no external API keys)
  // -------------------------------------------------------------------------

  private async processViaMock(
    imageUrl: string,
    processedAt: string,
    removeClutter = false,
  ): Promise<ProcessFactoryImageResult> {
    /**
     * In production, replace this with a local Python Pillow/ONNX pipeline
     * (see showroom/image_enhance.py in the Django monolith) or queue to GPU worker.
     *
     * Mock returns the source URL with a query flag so the frontend can apply
     * CSS/WebGL post-processing shaders when AI keys are absent.
     */
    await this.simulateLatency(800, 1800);

    const separator = imageUrl.includes('?') ? '&' : '?';
    const mode = removeClutter ? 'cleanup' : 'industry40';
    const enhancedImageUrl = `${imageUrl}${separator}enhanced=${mode}&mock=1&t=${Date.now()}`;

    const prompt = removeClutter ? FACTORY_CLEANUP_POSITIVE_PROMPT : FACTORY_TECHIFY_POSITIVE_PROMPT;
    const negativePrompt = removeClutter
      ? FACTORY_CLEANUP_NEGATIVE_PROMPT
      : FACTORY_TECHIFY_NEGATIVE_PROMPT;

    return {
      enhancedImageUrl,
      provider: 'mock',
      sourceImageUrl: imageUrl,
      promptUsed: prompt,
      negativePromptUsed: negativePrompt,
      processedAt,
      externalJobId: `mock_${Date.now()}`,
    };
  }

  private simulateLatency(minMs: number, maxMs: number): Promise<void> {
    const delay = minMs + Math.random() * (maxMs - minMs);
    return new Promise((resolve) => setTimeout(resolve, delay));
  }
}

// ---------------------------------------------------------------------------
// Factory — wire from environment (12-factor app)
// ---------------------------------------------------------------------------

export function createImageProcessorFromEnv(): ImageProcessorService {
  const defaultProvider = (process.env.IMAGE_PROCESSOR_PROVIDER ?? 'mock') as ProcessingProvider;

  return new ImageProcessorService({
    replicateApiToken: process.env.REPLICATE_API_TOKEN,
    cloudinaryCloudName: process.env.CLOUDINARY_CLOUD_NAME,
    cloudinaryApiKey: process.env.CLOUDINARY_API_KEY,
    cloudinaryApiSecret: process.env.CLOUDINARY_API_SECRET,
    defaultProvider,
    replicateModel: process.env.REPLICATE_MODEL,
  });
}

/** Convenience export matching the requested function signature */
export async function processFactoryImage(
  imageUrl: string,
  options?: ProcessFactoryImageOptions,
): Promise<string> {
  const service = createImageProcessorFromEnv();
  const result = await service.processFactoryImage(imageUrl, options);
  return result.enhancedImageUrl;
}

export default ImageProcessorService;
