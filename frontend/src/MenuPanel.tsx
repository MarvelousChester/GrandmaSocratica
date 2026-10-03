import type { CSSProperties } from 'react'
import { PencilIcon, PlusIcon, Rule, TrashIcon } from './Sketch'
import type { MenuItem } from './types'

interface Props {
  title: string
  side: 'left' | 'right'
  fill: string
  items: MenuItem[]
  onAdd: () => void
  onEdit: (item: MenuItem) => void
  onRemove: (item: MenuItem) => void
}

export function MenuPanel({ title, side, fill, items, onAdd, onEdit, onRemove }: Props) {
  return (
    <section
      className={`panel panel--${side}`}
      style={{ '--fill': fill } as CSSProperties}
      aria-label={title}
    >
      <h2 className="panel__title">{title}</h2>
      <Rule />
      <ul className="panel__list">
        {items.map((item) => (
          <li key={item.id}>
            <div className="row">
              <span className="row__name">{item.name}</span>
              <span className="row__price">${item.price.toFixed(2)}</span>
              <button
                type="button"
                className="icon-btn"
                aria-label={`Edit ${item.name}`}
                onClick={() => onEdit(item)}
              >
                <PencilIcon />
              </button>
              <button
                type="button"
                className="icon-btn"
                aria-label={`Remove ${item.name}`}
                onClick={() => onRemove(item)}
              >
                <TrashIcon />
              </button>
            </div>
            <Rule />
          </li>
        ))}
      </ul>
      <div className="panel__footer">
        <button
          type="button"
          className="sketch plus"
          aria-label={`Add menu item (${title})`}
          onClick={onAdd}
        >
          <PlusIcon />
        </button>
      </div>
    </section>
  )
}
