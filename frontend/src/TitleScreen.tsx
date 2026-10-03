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
        A corporate chain opened up right next door. Set the two menus, open the
        doors, and see who the town actually picks.
      </p>
      <button type="button" className="sketch start" onClick={onBegin}>
        Begin
      </button>
    </div>
  )
}
