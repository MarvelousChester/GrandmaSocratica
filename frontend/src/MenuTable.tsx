import { Badge, Group, NumberInput, Table, Text } from '@mantine/core'
import type { Daypart, MenuItem } from './types'

interface Props {
  items: MenuItem[]
  basePrices: Record<string, number>
  prices: Record<string, number>
  daypart: Daypart
  onPriceChange: (id: string, price: number) => void
}

export function MenuTable({ items, basePrices, prices, daypart, onPriceChange }: Props) {
  return (
    <Table.ScrollContainer minWidth={560}>
      <Table verticalSpacing="xs" highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Item</Table.Th>
            <Table.Th>Price</Table.Th>
            <Table.Th ta="right">Portion</Table.Th>
            <Table.Th ta="right">$/100g</Table.Th>
            <Table.Th ta="right">Pull</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {items.map((item) => {
            const price = prices[item.id]
            const delta = price - basePrices[item.id]
            return (
              <Table.Tr key={item.id}>
                <Table.Td>
                  <Text fw={500}>{item.name}</Text>
                  <Badge size="xs" variant="light" color="gray">
                    {item.category}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Group gap="xs" wrap="nowrap">
                    <NumberInput
                      aria-label={`${item.name} price`}
                      value={price}
                      onChange={(v) => typeof v === 'number' && onPriceChange(item.id, v)}
                      prefix="$"
                      min={0}
                      step={0.25}
                      decimalScale={2}
                      fixedDecimalScale
                      w={110}
                    />
                    {Math.abs(delta) > 0.001 && (
                      <Text size="xs" c={delta > 0 ? 'red' : 'teal'}>
                        {delta > 0 ? '+' : '−'}${Math.abs(delta).toFixed(2)}
                      </Text>
                    )}
                  </Group>
                </Table.Td>
                <Table.Td ta="right">{item.portion_size_g} g</Table.Td>
                <Table.Td ta="right">{((price / item.portion_size_g) * 100).toFixed(2)}</Table.Td>
                <Table.Td ta="right">{(item.daypart_weights[daypart] ?? 0.5).toFixed(2)}</Table.Td>
              </Table.Tr>
            )
          })}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  )
}
