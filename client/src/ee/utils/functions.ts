import api from "@/api";
import {
    PlaygroundParameters,
    PlaygroundSuccessResponse,
    PlaygroundErrorResponse, PlaygroundErrorDetail
} from "@/types/types";
import { useMutation } from "@tanstack/react-query";
import { AxiosError, AxiosResponse } from "axios";

interface PlaygroundErrorRawResponse {
  detail: PlaygroundErrorResponse
}

export type PlaygroundResult =
  | { success: true; data: PlaygroundSuccessResponse }
  | { success: false; error: PlaygroundErrorDetail };

/**
 * Function to call the playground API
 * Returns properly typed error or success response
 */
export const runPlayground = async (
  projectUuid: string,
  functionUuid: string,
  playgroundParameters: PlaygroundParameters
): Promise<PlaygroundResult> => {
  try {
    const response = await api.post<
      PlaygroundParameters,
      AxiosResponse<PlaygroundSuccessResponse>
    >(
      `/ee/projects/${projectUuid}/functions/${functionUuid}/playground`,
      playgroundParameters
    );

    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    if (error instanceof AxiosError && error.response?.data) {
      const errorResponse = error.response.data as PlaygroundErrorRawResponse;

      return {
        success: false,
        error: errorResponse.detail.error
      };
    }

    return {
      success: false,
      error: {
          type: "UnexpectedServerError",
          reason: "An error occurred on the client side",
          details: error instanceof Error ? error.message : String(error)
      }
    };
  }
};

/**
 * React Query mutation hook
 * Provides type-safe error handling
 */
export const useRunPlaygroundMutation = () => {
  return useMutation<
    PlaygroundResult,
    Error,
    {
      projectUuid: string;
      functionUuid: string;
      playgroundParameters: PlaygroundParameters;
    }
  >({
    mutationFn: async ({
      projectUuid,
      functionUuid,
      playgroundParameters,
    }) => await runPlayground(projectUuid, functionUuid, playgroundParameters),
  });
};
