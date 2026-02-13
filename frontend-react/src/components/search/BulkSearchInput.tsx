import { useCallback } from 'react'
import { FileUploadButton } from './FileUploadButton'
import { useFileImport } from '../../hooks/useFileImport'
import styles from './BulkSearchInput.module.css'

interface BulkSearchInputProps {
  value: string
  onChange: (value: string) => void
  disabled: boolean
}

export function BulkSearchInput({ value, onChange, disabled }: BulkSearchInputProps) {
  const { importFile } = useFileImport()

  const handleFile = useCallback(async (file: File) => {
    const ids = await importFile(file)
    if (ids.length > 0) {
      const existing = value.trim()
      const merged = existing ? existing + '\n' + ids.join('\n') : ids.join('\n')
      onChange(merged)
    }
  }, [importFile, value, onChange])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
  }, [])

  return (
    <div>
      <div className={styles.header}>
        <FileUploadButton onFileSelected={handleFile} disabled={disabled} />
        <span className={styles.hint}>or drag &amp; drop a .csv/.txt file onto the textarea</span>
      </div>
      <div className={styles.inputGroup}>
        <textarea
          className={styles.textarea}
          value={value}
          onChange={e => onChange(e.target.value)}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          placeholder={`Enter extension IDs, one per line\n\nExample:\ncjpalhdlnbpafiamejdnhcphjbkeiagm\nuBlock0@raymondhill.net\nodfafepnkmbhccpbejgmiehpchacaeak`}
          disabled={disabled}
        />
      </div>
      <p className={styles.help}>Tip: Enter one extension ID per line, or upload a CSV/TXT file</p>
    </div>
  )
}
