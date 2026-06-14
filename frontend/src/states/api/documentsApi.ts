import { baseApi } from "./baseApi";

export interface DocumentItem {
  id: number;
  title: string;
  document_type: string;
  access_level: string;
  content: string;
  summary?: string;
  keywords?: string;
  is_knowledge_base_enabled: boolean;
  version: number;
  created_by_email: string;
  last_updated_by_email: string;
  created_at: string;
  updated_at: string;
  last_updated_at?: string;
}

// Unified response envelope matching your backend's api_success utility
interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  meta?: { count: number };
}

export const documentsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // GET /api/documents/
    getDocuments: builder.query<ApiResponse<DocumentItem[]>, void>({
      query: () => "documents",
      providesTags: ["Documents"],
    }),

    // GET /api/documents/search/?title=...&is_knowledge_base_enabled=...
    // Adjusted from a plain string to an object to support multi-field DocumentQuerySerializer filtering
    searchDocuments: builder.query<
      ApiResponse<DocumentItem[]>,
      Record<string, any>
    >({
      query: (params) => ({
        url: "documents/search",
        method: "GET",
        params,
      }),
      providesTags: ["Documents"],
    }),

    // POST /api/documents/
    createDocument: builder.mutation<
      ApiResponse<DocumentItem>,
      Partial<DocumentItem>
    >({
      query: (newDoc) => ({
        url: "documents",
        method: "POST",
        body: newDoc,
      }),
      invalidatesTags: ["Documents"],
    }),

    // PATCH /api/documents/:id/
    updateDocument: builder.mutation<
      ApiResponse<DocumentItem>,
      { id: number; data: Partial<DocumentItem> }
    >({
      query: ({ id, data }) => ({
        url: `documents/${id}`,
        method: "PATCH",
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        "Documents",
        { type: "Documents", id },
      ],
    }),

    // DELETE /api/documents/:id/ (Triggers backend archive soft-delete)
    deleteDocument: builder.mutation<ApiResponse<null>, number>({
      query: (id) => ({
        url: `documents/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Documents"],
    }),

    // GET /api/documents/:id/
    getDocument: builder.query<ApiResponse<DocumentItem>, number>({
      query: (documentId) => `documents/${documentId}`,
      providesTags: (result, error, documentId) => [
        { type: "Documents", id: documentId },
      ],
    }),
  }),
});

export const {
  useGetDocumentsQuery,
  useSearchDocumentsQuery,
  useLazySearchDocumentsQuery,
  useCreateDocumentMutation,
  useUpdateDocumentMutation,
  useDeleteDocumentMutation,
  useGetDocumentQuery,
} = documentsApi;
