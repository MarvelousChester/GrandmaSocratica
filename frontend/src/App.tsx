import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  AppShell,
  Button,
  Card,
  Container,
  Group,
  Loader,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Title,
} from '@mantine/core'
import { fetchMenu } from './api'
import { BAKERY_LABELS, DAYPART_LABELS, DAYPARTS } from './constants'
import { MenuTable } from './MenuTable'
import type { Bakery, Daypart, MenuItem } from './types'

const BAKERIES = Object.keys(BAKERY_LABELS) as Bakery[]

export default function App() {
  const [menu, setMenu] = useState<MenuItem[] | null>(null)
  const [prices, setPrices] = useState<Record<string, number>>({})
  const [daypart, setDaypart] = useState<Daypart>('lunch')

  useEffect(() => {
    fetchMenu().then((items) => {
      setMenu(items)
      setPrices(Object.fromEntries(items.map((i) => [i.id, i.price])))
    })
  }, [])

  const basePrices = useMemo(
    () => Object.fromEntries((menu ?? []).map((i) => [i.id, i.price])),
    [menu],
  )

  const setPrice = (id: string, price: number) => setPrices((p) => ({ ...p, [id]: price }))
  const resetPrices = () => setPrices(basePrices)

  return (
    <AppShell header={{ height: 60 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Title order={3}>Bakery price simulator</Title>
          <Button variant="default" onClick={resetPrices} disabled={!menu}>
            Reset prices
          </Button>
        </Group>
      </AppShell.Header>

      <AppShell.Main>
        <Container size="xl">
          {!menu ? (
            <Loader />
          ) : (
            <Stack>
              <Group>
                <SegmentedControl
                  value={daypart}
                  onChange={(v) => setDaypart(v as Daypart)}
                  data={DAYPARTS.map((d) => ({ value: d, label: DAYPART_LABELS[d] }))}
                />
              </Group>

              <Alert variant="light" title="Using mock menu data">
                Edit prices below. Simulation results will show up here once the backend exposes them.
              </Alert>

              <SimpleGrid cols={{ base: 1, lg: 2 }}>
                {BAKERIES.map((bakery) => (
                  <Card key={bakery} withBorder padding="md">
                    <Title order={4} mb="sm">
                      {BAKERY_LABELS[bakery]}
                    </Title>
                    <MenuTable
                      items={menu.filter((i) => i.bakery === bakery)}
                      basePrices={basePrices}
                      prices={prices}
                      daypart={daypart}
                      onPriceChange={setPrice}
                    />
                  </Card>
                ))}
              </SimpleGrid>
            </Stack>
          )}
        </Container>
      </AppShell.Main>
    </AppShell>
  )
}
