import { useEffect, useRef, useState } from 'react'
import { suggestLocations, reverseGeocode } from '../api'

const DEBOUNCE_MS = 400
const MIN_CHARS = 3

export default function LocationInput({ label, name, value, onChange, placeholder, allowMyLocation }) {
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [locating, setLocating] = useState(false)
  const [locateError, setLocateError] = useState(null)
  const skipNextFetch = useRef(false)
  const debounceRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    if (skipNextFetch.current) {
      skipNextFetch.current = false
      return
    }
    clearTimeout(debounceRef.current)
    if (value.trim().length < MIN_CHARS) {
      setSuggestions([])
      return
    }
    debounceRef.current = setTimeout(async () => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      setLoading(true)
      try {
        const results = await suggestLocations(value.trim(), controller.signal)
        setSuggestions(results)
        setOpen(true)
      } catch (err) {
        if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
          setSuggestions([])
        }
      } finally {
        setLoading(false)
      }
    }, DEBOUNCE_MS)
    return () => clearTimeout(debounceRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  function selectSuggestion(suggestion) {
    skipNextFetch.current = true
    setSuggestions([])
    setOpen(false)
    onChange(suggestion.display_name)
  }

  function handleUseMyLocation() {
    if (!navigator.geolocation) {
      setLocateError('Geolocation is not supported by this browser')
      return
    }
    setLocating(true)
    setLocateError(null)
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const displayName = await reverseGeocode(position.coords.latitude, position.coords.longitude)
          skipNextFetch.current = true
          onChange(displayName)
        } catch {
          setLocateError('Could not resolve your location to an address')
        } finally {
          setLocating(false)
        }
      },
      () => {
        setLocateError('Location permission denied')
        setLocating(false)
      },
      { timeout: 10000 }
    )
  }

  return (
    <div className="location-input">
      <label>
        <span className="location-input__label-row">
          {label}
          {allowMyLocation && (
            <button
              type="button"
              className="location-input__locate-btn"
              onClick={handleUseMyLocation}
              disabled={locating}
              title="Use my current location"
            >
              {locating ? 'Locating…' : '📍 Use my location'}
            </button>
          )}
        </span>
        <div className="location-input__field">
          <input
            name={name}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => suggestions.length > 0 && setOpen(true)}
            onBlur={() => setTimeout(() => setOpen(false), 150)}
            placeholder={placeholder}
            autoComplete="off"
            required
          />
          {loading && <span className="location-input__spinner" aria-hidden="true" />}
        </div>
      </label>

      {open && suggestions.length > 0 && (
        <ul className="location-input__suggestions">
          {suggestions.map((s, i) => (
            <li key={i}>
              <button type="button" onMouseDown={() => selectSuggestion(s)}>
                {s.display_name}
              </button>
            </li>
          ))}
        </ul>
      )}

      {locateError && <div className="location-input__error">{locateError}</div>}
    </div>
  )
}
