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

/// One optional overcharge per arena. Pickup and firing are separate so an
/// already spawned projectile keeps its original damage.
#[derive(Debug, Default, PartialEq, Eq)]
pub enum ChargePad {
    #[default]
    Available,
    Armed,
    Spent,
}

impl ChargePad {
    pub fn available(&self) -> bool {
        *self == Self::Available
    }

    pub fn armed(&self) -> bool {
        *self == Self::Armed
    }

    pub fn collect(&mut self, x: f32, y: f32, z: f32) -> bool {
        if self.available() && (-0.2..=2.0).contains(&y) && x * x + z * z <= 1.6 * 1.6 {
            *self = Self::Armed;
            true
        } else {
            false
        }
    }

    pub fn next_damage(&mut self) -> f32 {
        if self.armed() {
            *self = Self::Spent;
            PROJECTILE_DAMAGE * 2.0
        } else {
            PROJECTILE_DAMAGE
        }
    }
}

#[cfg(test)]
mod charge_tests {
    use super::*;

    #[test]
    fn pad_cannot_be_collected_from_spawn_or_above() {
        let mut pad = ChargePad::default();
        assert!(!pad.collect(4.0, 1.0, -4.0));
        assert!(!pad.collect(0.0, 2.1, 0.0));
        assert!(!pad.collect(f32::NAN, 1.0, 0.0));
        assert!(pad.collect(1.59, 1.0, 0.0));
    }

    #[test]
    fn overcharge_is_one_shot_and_does_not_upgrade_in_flight_shots() {
        let mut pad = ChargePad::default();
        let normal_shot_before_pickup = pad.next_damage();
        assert!(pad.collect(0.0, 1.0, 0.0));
        assert!(!pad.collect(0.0, 1.0, 0.0));
        let charged_shot = pad.next_damage();
        let normal_shot_after_pickup = pad.next_damage();
        assert!(!pad.collect(0.0, 1.0, 0.0));

        let mut target = Combat::default();
        target.damage(normal_shot_before_pickup);
        assert_eq!(target.hp, 75.0);
        target.damage(charged_shot);
        assert_eq!(target.hp, 25.0);
        target.damage(normal_shot_after_pickup);
        assert!(target.destroyed());

        pad = ChargePad::default();
        assert!(pad.collect(0.0, 1.0, 0.0));
    }
}
