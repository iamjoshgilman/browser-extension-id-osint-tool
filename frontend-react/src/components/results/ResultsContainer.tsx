import type { ExtensionData } from '../../types/extension'
import { ResultCard } from './ResultCard'
import { ExportToolbar } from './ExportToolbar'
import { Spinner } from '../common/Spinner'
import { ErrorBanner } from '../common/ErrorBanner'
import styles from './ResultsContainer.module.css'

interface ResultsContainerProps {
  results: ExtensionData[]
  loading: boolean
  error: string | null
  query: string
  stores: string[]
  totalSearched?: number
}

export function ResultsContainer({
  results,
  loading,
  error,
  query,
  stores,
  totalSearched,
}: ResultsContainerProps) {
  if (loading) {
    return <Spinner message="Searching extensions..." />
  }

  if (error && results.length === 0) {
    return <ErrorBanner message={error} />
  }

  if (results.length === 0) return null

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>
          {totalSearched != null
            ? `Bulk Search Results`
            : `Extension ID: ${query}`}
        </h2>
        {totalSearched != null && (
          <span className={styles.count}>
            {results.length} result{results.length !== 1 ? 's' : ''} from {totalSearched} IDs
          </span>
        )}
      </div>

      <ExportToolbar results={results} query={query} stores={stores} />

      {results.map((ext, i) => (
        <ResultCard key={`${ext.extension_id}-${ext.store_source}-${i}`} extension={ext} />
      ))}
    </div>
  )
}
