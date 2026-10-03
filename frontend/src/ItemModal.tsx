import { Modal } from '@mantine/core'
import { blankItem } from './data'
import { ItemForm } from './ItemForm'
import type { Bakery, MenuItem } from './types'

// What the modal was opened for: a new item on a bakery's menu, or an existing one.
export type ModalTarget = { kind: 'add'; bakery: Bakery } | { kind: 'edit'; item: MenuItem }

interface Props {
  opened: boolean
  target: ModalTarget | null
  onClose: () => void
  onSave: (item: MenuItem) => void
}

export function ItemModal({ opened, target, onClose, onSave }: Props) {
  const title = target?.kind === 'edit' ? `Edit ${target.item.name}` : 'Add menu item'
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={title}
      size="lg"
      yOffset="8vh" // top-anchored so switching tabs doesn't make it jump
      // An accidental click outside shouldn't throw away edits.
      closeOnClickOutside={false}
      classNames={{
        content: 'sketch sk-modal',
        header: 'sk-modal__header',
        title: 'sk-modal__title',
        close: 'sk-modal__close',
      }}
    >
      {target?.kind === 'edit' && (
        <ItemForm key={target.item.id} item={target.item} submitLabel="Save" onSave={onSave} onCancel={onClose} />
      )}
      {target?.kind === 'add' && (
        <ItemForm
          key={`add-${target.bakery}`}
          item={blankItem(target.bakery)}
          submitLabel="Add item"
          onSave={onSave}
          onCancel={onClose}
        />
      )}
    </Modal>
  )
}
