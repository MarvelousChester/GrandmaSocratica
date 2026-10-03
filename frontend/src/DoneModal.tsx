import { Button, Group, Modal, Stack, Table, Text } from '@mantine/core'
import { BAKERY_INFO, PANEL_ORDER } from './data'
import type { DayResult } from './types'

interface Props {
  opened: boolean
  day: DayResult
  onClose: () => void
}

const money = (n: number) => `${n < 0 ? '−' : ''}$${Math.abs(n).toFixed(2)}`

/** End-of-day results: who won on revenue, and the final totals. */
export function DoneModal({ opened, day, onClose }: Props) {
  const { summary, ledger } = day
  const [a, b] = PANEL_ORDER.map((bakery) => summary.by_bakery[bakery].revenue)
  const winner =
    Math.abs(a - b) < 0.005
      ? "It's a tie!"
      : `${BAKERY_INFO[a > b ? PANEL_ORDER[0] : PANEL_ORDER[1]].label} wins the day!`

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="YAY!"
      size="lg"
      centered
      closeOnClickOutside={false}
      classNames={{
        content: 'sketch sk-modal',
        header: 'sk-modal__header',
        title: 'sk-modal__title sk-modal__title--yay',
        close: 'sk-modal__close',
      }}
    >
      <Stack>
        <Text className="done__winner">{winner}</Text>
        <div className="sketch sk-box">
          <Table className="done__table" withRowBorders={false}>
            <Table.Thead>
              <Table.Tr>
                <Table.Th />
                {PANEL_ORDER.map((bakery) => (
                  <Table.Th key={bakery} ta="right">
                    {BAKERY_INFO[bakery].label}
                  </Table.Th>
                ))}
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              <Table.Tr>
                <Table.Td>Revenue</Table.Td>
                {PANEL_ORDER.map((bakery) => (
                  <Table.Td key={bakery} ta="right">{money(summary.by_bakery[bakery].revenue)}</Table.Td>
                ))}
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Profit</Table.Td>
                {PANEL_ORDER.map((bakery) => (
                  <Table.Td key={bakery} ta="right">
                    {ledger ? money(ledger.bakeries[bakery].financials.profit) : '—'}
                  </Table.Td>
                ))}
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Items sold</Table.Td>
                {PANEL_ORDER.map((bakery) => (
                  <Table.Td key={bakery} ta="right">{summary.by_bakery[bakery].purchases}</Table.Td>
                ))}
              </Table.Tr>
            </Table.Tbody>
          </Table>
        </div>
        <Text>
          {summary.visits} customers came by; {summary.walkaways} left without buying anything.
        </Text>
        <Group justify="flex-end">
          <Button className="sk-btn sk-btn--primary" onClick={onClose}>
            Back to menus
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
