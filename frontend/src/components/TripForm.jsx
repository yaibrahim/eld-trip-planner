import { useState } from 'react'

const initialState = {
  current_location: '',
  pickup_location: '',
  dropoff_location: '',
  current_cycle_used: '',
}

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState(initialState)

  function handleChange(e) {
    const { name, value } = e.target
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

      <label>
        Current Location
        <input
          name="current_location"
          value={form.current_location}
          onChange={handleChange}
          placeholder="e.g. Chicago, IL"
          required
        />
      </label>

      <label>
        Pickup Location
        <input
          name="pickup_location"
          value={form.pickup_location}
          onChange={handleChange}
          placeholder="e.g. Indianapolis, IN"
          required
        />
      </label>

      <label>
        Dropoff Location
        <input
          name="dropoff_location"
          value={form.dropoff_location}
          onChange={handleChange}
          placeholder="e.g. Dallas, TX"
          required
        />
      </label>

      <label>
        Current Cycle Used (Hrs)
        <input
          name="current_cycle_used"
          type="number"
          min="0"
          max="70"
          step="0.5"
          value={form.current_cycle_used}
          onChange={handleChange}
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
