export interface MetadataRequest {
  url: string;
}

export interface VideoMetadataResponse {
  title: string;
  channel: string;
  duration_seconds: number;
  needs_confirmation: boolean;
  estimated_minutes: number | null;
}

export interface VideoMeta {
  video_id: string;
  title: string;
  channel: string;
  duration_seconds: number;
  date_added: string;
  source_url: string;
}

export interface DownloadStartedResponse {
  video_id: string;
  status: string;
}

export interface DownloadStatusResponse {
  status: string;
  error?: string | null;
}

export interface TrimRequest {
  start_seconds: number;
  end_seconds: number;
}

export interface TrimResponse {
  status: string;
  duration_seconds: number;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

export type TranscriptionMethod = 'local' | 'api';

export interface Transcript {
  text: string;
  segments: TranscriptSegment[];
  method: TranscriptionMethod;
}

export interface TranscribeRequest {
  method: TranscriptionMethod;
}

export interface TranscriptionStartedResponse {
  video_id: string;
  status: string;
}

export interface TranscriptionStatusResponse {
  status: string;
  error?: string | null;
}

export type SummarizationProvider = 'anthropic' | 'openai';

export interface SummarizeRequest {
  provider: SummarizationProvider;
}

export interface SummarizationStartedResponse {
  video_id: string;
  status: string;
}

export interface SummarizationStatusResponse {
  status: string;
  error?: string | null;
}

export interface SummaryEntry {
  created_at: string;
  content: string;
}

export interface SummaryListResponse {
  summaries: SummaryEntry[];
}

export interface VideoSummary {
  video_id: string;
  title: string;
  channel: string;
  duration_seconds: number;
  date_added: string;
}

export interface VideoListResponse {
  videos: VideoSummary[];
}

export interface VideoListParams {
  search?: string;
  date_from?: string;
  date_to?: string;
}
