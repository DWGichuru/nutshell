import type {
  DownloadStartedResponse,
  DownloadStatusResponse,
  SummarizationProvider,
  SummarizationStartedResponse,
  SummarizationStatusResponse,
  SummaryListResponse,
  Transcript,
  TranscriptionMethod,
  TranscriptionStartedResponse,
  TranscriptionStatusResponse,
  TrimResponse,
  VideoListParams,
  VideoListResponse,
  VideoMeta,
  VideoMetadataResponse,
} from './types';

const BASE_URL = '/api/videos';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail =
      body !== null && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
        ? body.detail
        : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

function jsonBody(body: unknown): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
}

export function previewMetadata(url: string): Promise<VideoMetadataResponse> {
  return request(`${BASE_URL}/metadata`, jsonBody({ url }));
}

export function startDownload(url: string): Promise<DownloadStartedResponse> {
  return request(`${BASE_URL}/download`, jsonBody({ url }));
}

export function getDownloadStatus(videoId: string): Promise<DownloadStatusResponse> {
  return request(`${BASE_URL}/${videoId}/status`);
}

export function audioUrl(videoId: string): string {
  return `${BASE_URL}/${videoId}/audio`;
}

export function trimAudio(
  videoId: string,
  startSeconds: number,
  endSeconds: number,
): Promise<TrimResponse> {
  return request(
    `${BASE_URL}/${videoId}/trim`,
    jsonBody({ start_seconds: startSeconds, end_seconds: endSeconds }),
  );
}

export function startTranscription(
  videoId: string,
  method: TranscriptionMethod,
): Promise<TranscriptionStartedResponse> {
  return request(`${BASE_URL}/${videoId}/transcribe`, jsonBody({ method }));
}

export function getTranscriptionStatus(videoId: string): Promise<TranscriptionStatusResponse> {
  return request(`${BASE_URL}/${videoId}/transcription/status`);
}

export function getTranscript(videoId: string): Promise<Transcript> {
  return request(`${BASE_URL}/${videoId}/transcript`);
}

export function startSummarization(
  videoId: string,
  provider: SummarizationProvider,
): Promise<SummarizationStartedResponse> {
  return request(`${BASE_URL}/${videoId}/summarize`, jsonBody({ provider }));
}

export function getSummarizationStatus(videoId: string): Promise<SummarizationStatusResponse> {
  return request(`${BASE_URL}/${videoId}/summarization/status`);
}

export function getSummaries(videoId: string): Promise<SummaryListResponse> {
  return request(`${BASE_URL}/${videoId}/summaries`);
}

export function listVideos(params: VideoListParams = {}): Promise<VideoListResponse> {
  const query = new URLSearchParams();
  if (params.search) query.set('search', params.search);
  if (params.date_from) query.set('date_from', params.date_from);
  if (params.date_to) query.set('date_to', params.date_to);
  const suffix = query.toString();
  return request(`${BASE_URL}${suffix ? `?${suffix}` : ''}`);
}

export function getVideo(videoId: string): Promise<VideoMeta> {
  return request(`${BASE_URL}/${videoId}`);
}
