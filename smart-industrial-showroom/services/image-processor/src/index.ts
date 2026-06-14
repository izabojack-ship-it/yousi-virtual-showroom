import express from 'express';
import cors from 'cors';
import { z } from 'zod';
import {
  createImageProcessorFromEnv,
  processFactoryImage,
} from './services/imageProcessor.service.js';

const app = express();
const PORT = Number(process.env.PORT ?? 4100);

app.use(cors({ origin: process.env.CORS_ORIGIN ?? '*' }));
app.use(express.json({ limit: '10mb' }));

const ProcessBodySchema = z.object({
  imageUrl: z.string().url(),
  provider: z.enum(['replicate', 'cloudinary', 'mock']).optional(),
  strength: z.number().min(0.1).max(0.95).optional(),
  removeClutter: z.boolean().optional(),
});

/** POST /api/v1/process — full result payload */
app.post('/api/v1/process', async (req, res) => {
  try {
    const body = ProcessBodySchema.parse(req.body);
    const service = createImageProcessorFromEnv();
    const result = await service.processFactoryImage(body.imageUrl, {
      provider: body.provider,
      strength: body.strength,
      removeClutter: body.removeClutter,
    });
    res.json({ success: true, data: result });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Processing failed';
    res.status(400).json({ success: false, error: message });
  }
});

/** POST /api/v1/process/url — convenience: returns enhanced URL only */
app.post('/api/v1/process/url', async (req, res) => {
  try {
    const body = ProcessBodySchema.parse(req.body);
    const url = await processFactoryImage(body.imageUrl, {
      provider: body.provider,
      strength: body.strength,
      removeClutter: body.removeClutter,
    });
    res.json({ success: true, enhancedImageUrl: url });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Processing failed';
    res.status(400).json({ success: false, error: message });
  }
});

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'image-processor' });
});

app.listen(PORT, () => {
  console.log(`[image-processor] listening on http://localhost:${PORT}`);
});
