import { useState } from 'react'
import LocationInput from './LocationInput'

const initialState = {
  current_location: '',
  pickup_location: '',
  dropoff_location: '',
  current_cycle_used: '',
}

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState(initialState)

  function setField(name, value) {
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      ...form,
      current_cycle_used: parseFloat(form.current_cycle_used || '0'),
    })
  }

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <h2>Plan a Trip</h2>

      <LocationInput
        label="Current Location"
        name="current_location"
        value={form.current_location}
        onChange={(v) => setField('current_location', v)}
        placeholder="e.g. Chicago, IL"
        allowMyLocation
      />

      <LocationInput
        label="Pickup Location"
        name="pickup_location"
        value={form.pickup_location}
        onChange={(v) => setField('pickup_location', v)}
        placeholder="e.g. Indianapolis, IN"
      />

      <LocationInput
        label="Dropoff Location"
        name="dropoff_location"
        value={form.dropoff_location}
        onChange={(v) => setField('dropoff_location', v)}
        placeholder="e.g. Dallas, TX"
      />

      <label>
        Current Cycle Used (Hrs)
        <input
          name="current_cycle_used"
          type="number"
          min="0"
          max="70"
          step="0.5"
          value={form.current_cycle_used}
          onChange={(e) => setField('current_cycle_used', e.target.value)}
          placeholder="0"
          required
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? 'Planning…' : 'Plan Trip'}
      </button>
    </form>
  )
}
