import request from '@/utils/request'
import type { QuestionRecognitionResult } from '@/types/api'

export const questionRecognitionApi = {
  recognize: (imageBase64: string) => request.post<unknown, QuestionRecognitionResult>(
    '/question-recognition/recognize',
    { imageBase64 },
    { timeout: 120_000, silent: true },
  ),
}
