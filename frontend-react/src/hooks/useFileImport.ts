import { useCallback } from 'react'
import { parseFile } from '../utils/fileParser'

interface UseFileImportReturn {
  importFile: (file: File) => Promise<string[]>
}

const MAX_FILE_SIZE = 1024 * 1024 // 1 MB

export function useFileImport(): UseFileImportReturn {
  const importFile = useCallback(async (file: File): Promise<string[]> => {
    if (file.size > MAX_FILE_SIZE) {
      throw new Error('File too large. Maximum size is 1MB.')
    }
    const text = await file.text()
    return parseFile(text)
  }, [])

  return { importFile }
}
