import { useCallback } from 'react'
import type { ExtensionData } from '../types/extension'
import { exportCsv, exportJson } from '../utils/export'

interface UseExportReturn {
  downloadCsv: (results: ExtensionData[], query: string) => void
  downloadJson: (results: ExtensionData[], query: string, stores: string[]) => void
}

export function useExport(): UseExportReturn {
  const downloadCsv = useCallback((results: ExtensionData[], query: string) => {
    exportCsv(results, query)
  }, [])

  const downloadJson = useCallback((results: ExtensionData[], query: string, stores: string[]) => {
    exportJson(results, query, stores)
  }, [])

  return { downloadCsv, downloadJson }
}
