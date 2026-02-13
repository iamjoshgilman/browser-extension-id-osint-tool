import { useRef } from 'react'
import styles from './FileUploadButton.module.css'

interface FileUploadButtonProps {
  onFileSelected: (file: File) => void
  disabled: boolean
}

export function FileUploadButton({ onFileSelected, disabled }: FileUploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileSelected(file)
      // Reset so the same file can be re-selected
      e.target.value = ''
    }
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.txt"
        onChange={handleChange}
        className={styles.hidden}
        disabled={disabled}
      />
      <button
        type="button"
        className={styles.button}
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
      >
        Upload File
      </button>
    </>
  )
}
