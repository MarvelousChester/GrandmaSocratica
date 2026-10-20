import logo from './logo.png'

/**
 * The opening card: the logo over the empty street, before either menu is up.
 *
 * It exists so the logo has room. Shown between the two menu panels it had a
 * quarter of the width to live in and collided with both headers.
 */
export function TitleScreen({ onBegin }: { onBegin: () => void }) {
  return (
    <div className="title">
      <img className="title__logo" src={logo} alt="Grandma must win" />
      <p className="title__tagline">
        The corporate chain <span className="title__bakery-chain">The Bakery</span> opened up next door to{' '}
        <span className="title__grandma-bakery">Grandma's Bakeria</span> with a suspiciously similar menu.
        <br />
        Optimize Grandma's costs and menu, and launch your attack!
      </p>
      <button type="button" className="sketch start" onClick={onBegin}>
        BEGIN
      </button>
    </div>
  )
}
