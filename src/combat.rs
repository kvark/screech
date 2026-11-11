/// Health for the repeatable parked-target encounter.
#[derive(Debug, Clone, Copy)]
pub struct Combat {
    pub hp: f32,
}

pub const MAX_HP: f32 = 100.0;
pub const PROJECTILE_DAMAGE: f32 = 25.0;

impl Default for Combat {
    fn default() -> Self {
        Self { hp: MAX_HP }
    }
}

impl Combat {
    pub fn destroyed(self) -> bool {
        self.hp <= 0.0
    }

    pub fn damage(&mut self, amount: f32) {
        if amount.is_finite() && amount > 0.0 {
            self.hp = (self.hp - amount).max(0.0);
        }
    }

    pub fn reset(&mut self) {
        *self = Self::default();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn four_projectiles_destroy_the_target() {
        let mut combat = Combat::default();
        for remaining in [75.0, 50.0, 25.0, 0.0] {
            combat.damage(PROJECTILE_DAMAGE);
            assert_eq!(combat.hp, remaining);
            assert_eq!(combat.destroyed(), remaining == 0.0);
        }
        combat.damage(PROJECTILE_DAMAGE);
        assert_eq!(combat.hp, 0.0);
    }

    #[test]
    fn restart_restores_a_damaged_or_destroyed_target() {
        let mut combat = Combat::default();
        for damage in [PROJECTILE_DAMAGE, MAX_HP, MAX_HP * 2.0] {
            combat.damage(damage);
            combat.reset();
            assert_eq!(combat.hp, MAX_HP);
            assert!(!combat.destroyed());
        }
    }

    #[test]
    fn invalid_damage_cannot_heal_or_corrupt_health() {
        let mut combat = Combat::default();
        for amount in [-25.0, f32::NAN, f32::INFINITY] {
            combat.damage(amount);
            assert_eq!(combat.hp, MAX_HP);
        }
    }
}
