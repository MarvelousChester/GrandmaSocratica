import { useState } from 'react'
import {
  Button,
  Chip,
  Group,
  NumberInput,
  Select,
  Slider,
  Stack,
  Tabs,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core'
import { ALLERGENS, FLAVOR_CATEGORIES, humanize, ITEM_CATEGORIES } from './data'
import type { FlavorProfile, ItemCategory, MenuItem } from './types'

// Price and portion hold whatever NumberInput reports -- a number, or a string
// such as '7.00', '7.' or '' mid-typing -- so a draft can be invalid.
// Daypart weights aren't user-editable, so they aren't in the draft and `build()`
// carries the item's own through.
type Draft = Omit<MenuItem, 'id' | 'bakery' | 'price' | 'portion_size_g' | 'daypart_weights'> & {
  price: number | string
  portion_size_g: number | string
}

/** NaN when the field is empty or not a number. */
const toNumber = (v: number | string) => (typeof v === 'number' ? v : v === '' ? NaN : Number(v))

function toDraft(item: MenuItem): Draft {
  return {
    name: item.name,
    category: item.category,
    description: item.description,
    flavor: item.flavor,
    price: item.price,
    portion_size_g: item.portion_size_g,
    allergens: item.allergens,
  }
}

interface MeterProps {
  label: string
  value: number
  min: number
  max: number
  marks: { value: number; label?: string }[]
  signed?: boolean
  onChange: (value: number) => void
}

function Meter({ label, value, min, max, marks, signed, onChange }: MeterProps) {
  return (
    <div>
      <Group justify="space-between">
        <Text size="sm" fw={500}>
          {label}
        </Text>
        <Text size="sm" c="dimmed">
          {signed && value > 0 ? '+' : ''}
          {value.toFixed(2)}
        </Text>
      </Group>
      {/* Inset so the end-mark labels, which centre on the ends, aren't clipped. */}
      <div style={{ padding: '0 28px' }}>
        <Slider
          value={value}
          onChange={onChange}
          min={min}
          max={max}
          step={0.05}
          size={16}
          thumbSize={24}
          color="#f8c9c9"
          marks={marks}
          label={null}
          mb="xl"
        />
      </div>
    </div>
  )
}

interface Props {
  item: MenuItem
  submitLabel: string
  onSave: (item: MenuItem) => void
  onCancel: () => void
}

export function ItemForm({ item, submitLabel, onSave, onCancel }: Props) {
  const [draft, setDraft] = useState(() => toDraft(item))
  // A blank name on a new item isn't an error until the user has touched it.
  const [nameTouched, setNameTouched] = useState(false)

  const set = <K extends keyof Draft>(key: K, value: Draft[K]) =>
    setDraft((d) => ({ ...d, [key]: value }))
  const setFlavor = (patch: Partial<FlavorProfile>) => set('flavor', { ...draft.flavor, ...patch })

  /** The edited item, or null while the draft breaks a backend constraint. */
  const build = (): MenuItem | null => {
    const price = toNumber(draft.price)
    const portion_size_g = toNumber(draft.portion_size_g)
    if (!draft.name.trim()) return null
    if (!(price >= 0)) return null
    if (!(portion_size_g > 0)) return null
    return { ...item, ...draft, name: draft.name.trim(), price, portion_size_g }
  }
  const valid = build() !== null

  const save = () => {
    const edited = build()
    if (edited) onSave(edited)
  }

  return (
    <Stack gap="md">
      <Tabs defaultValue="details">
        <Tabs.List>
          <Tabs.Tab value="details">Details</Tabs.Tab>
          <Tabs.Tab value="flavour">Flavour</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="details" pt="md">
          <Stack className="sketch sk-box">
            <TextInput
              label="Name"
              value={draft.name}
              onChange={(e) => {
                setNameTouched(true)
                set('name', e.currentTarget.value)
              }}
              error={nameTouched && !draft.name.trim() ? 'Required' : undefined}
              data-autofocus
            />
            <Select
              label="Category"
              data={ITEM_CATEGORIES.map((c) => ({ value: c, label: humanize(c) }))}
              value={draft.category}
              onChange={(v) => v && set('category', v as ItemCategory)}
              allowDeselect={false}
            />
            <Textarea
              label="Description"
              value={draft.description}
              onChange={(e) => set('description', e.currentTarget.value)}
              autosize
              minRows={2}
            />
            <Group grow align="flex-start">
              <NumberInput
                label="Price"
                value={draft.price}
                onChange={(v) => set('price', v)}
                prefix="$"
                min={0}
                step={0.25}
                decimalScale={2}
                fixedDecimalScale
                error={Number.isNaN(toNumber(draft.price)) ? 'Required' : undefined}
              />
              <NumberInput
                label="Portion size"
                value={draft.portion_size_g}
                onChange={(v) => set('portion_size_g', v)}
                suffix=" g"
                min={1}
                step={10}
                allowDecimal={false}
                error={Number.isNaN(toNumber(draft.portion_size_g)) ? 'Required' : undefined}
              />
            </Group>
            <div>
              <Text size="sm" fw={500} mb={6}>
                Allergens
              </Text>
              <Chip.Group
                multiple
                value={draft.allergens}
                onChange={(v) => set('allergens', v as MenuItem['allergens'])}
              >
                <Group gap="xs">
                  {ALLERGENS.map((a) => (
                    <Chip key={a} value={a} size="xs">
                      {humanize(a)}
                    </Chip>
                  ))}
                </Group>
              </Chip.Group>
            </div>
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value="flavour" pt="md">
          <Stack gap="xs" className="sketch sk-box">
            <Meter
              label="Sweet / savoury"
              value={draft.flavor.sweet_savoury}
              min={-1}
              max={1}
              signed
              marks={[{ value: -1, label: 'Savoury' }, { value: 0 }, { value: 1, label: 'Sweet' }]}
              onChange={(v) => setFlavor({ sweet_savoury: v })}
            />
            <Meter
              label="Bitterness"
              value={draft.flavor.bitterness}
              min={0}
              max={1}
              marks={[{ value: 0, label: 'None' }, { value: 1, label: 'Bitter' }]}
              onChange={(v) => setFlavor({ bitterness: v })}
            />
            <Meter
              label="Fruitiness"
              value={draft.flavor.fruitiness}
              min={0}
              max={1}
              marks={[{ value: 0, label: 'None' }, { value: 1, label: 'Fruity' }]}
              onChange={(v) => setFlavor({ fruitiness: v })}
            />
            <div>
              <Text size="sm" fw={500} mb={6}>
                Tastes of
              </Text>
              <Chip.Group
                multiple
                value={draft.flavor.categories}
                onChange={(v) => setFlavor({ categories: v as FlavorProfile['categories'] })}
              >
                <Group gap="xs">
                  {FLAVOR_CATEGORIES.map((c) => (
                    <Chip key={c} value={c} size="xs">
                      {humanize(c)}
                    </Chip>
                  ))}
                </Group>
              </Chip.Group>
            </div>
          </Stack>
        </Tabs.Panel>
      </Tabs>

      <Group justify="flex-end">
        <Button className="sk-btn" onClick={onCancel}>
          Cancel
        </Button>
        <Button className="sk-btn sk-btn--primary" onClick={save} disabled={!valid}>
          {submitLabel}
        </Button>
      </Group>
    </Stack>
  )
}
