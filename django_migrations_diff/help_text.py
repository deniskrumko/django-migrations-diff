HELP = """
<g>mdiff</g> is a CLI to compare Django migrations between two snapshots.

  Find more information at: https://github.com/deniskrumko/django-migrations-diff

<g>Basic Commands</g>

  mdiff <b><name></b>\t\t\tCreate snapshot
  mdiff <b><name_1></b> <b><name_2></b>\tCompare two snapshots

  mdiff <g>list</g>\t\t\tList of all snapshots

  mdiff <g>rm all</g></b>\t\t\tRemove all snapshots
  mdiff <g>rm</g> <b><name_1></b> <b><name_2></b>\tRemove specific snapshots

""".rstrip() # noqa
