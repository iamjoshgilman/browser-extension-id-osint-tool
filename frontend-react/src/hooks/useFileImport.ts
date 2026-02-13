import { useCallback } from 'react'
import { parseFile } from '../utils/fileParser'

interface UseFileImportReturn {
  importFile: (file: File) => Promise<string[]>
}

export function useFileImport(): UseFileImportReturn {
  const importFile = useCallback(async (file: File): Promise<string[]> => {
    const text = await file.text()
    return parseFile(text)
  }, [])

  return { importFile }
}
